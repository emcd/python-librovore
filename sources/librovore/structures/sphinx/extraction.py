# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#  You may obtain a copy of the License at                                   #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Documentation extraction and content retrieval. '''


from bs4 import BeautifulSoup as _BeautifulSoup

from . import __
from . import urls as _urls
from .patterns import THEME_PATTERNS as _THEME_PATTERNS
from .patterns import UNIVERSAL_PATTERNS as _UNIVERSAL_PATTERNS


_scribe = __.acquire_scribe( __name__ )


async def extract_contents(
    auxdata: __.ApplicationGlobals,
    source: str,
    objects: __.cabc.Sequence[ __.InventoryObject ], /, *,
    theme: __.Absential[ str ] = __.absent,
) -> list[ __.ContentDocument ]:
    ''' Extracts documentation content for specified objects. '''
    base_url = _urls.normalize_base_url( source )
    if not objects: return [ ]
    tasks = [
        _extract_object_documentation(
            auxdata, base_url, source, obj, theme )
        for obj in objects ]
    candidate_results = await __.asyncf.gather_async(
        *tasks, return_exceptions = True )
    results: list[ __.ContentDocument ] = [
        result.value for result in candidate_results
        if __.generics.is_value( result ) and result.value is not None ]
    return results


def parse_documentation_html(
    content: str, element_id: str, url: str, *,
    theme: __.Absential[ str ] = __.absent
) -> __.cabc.Mapping[ str, str ]:
    ''' Parses HTML content to extract documentation sections. '''
    try: soup = _BeautifulSoup( content, 'lxml' )
    except Exception as exc:
        raise __.DocumentationParseFailure(
            element_id, exc ) from exc
    # Theme should be provided from detection metadata
    # If absent, use None to fall back to generic detection
    container = _find_main_content_container( soup, theme )
    if __.is_absent( container ):
        raise __.DocumentationContentAbsence( element_id )
    element = container.find( id = element_id )
    if not element:
        raise __.DocumentationObjectAbsence( element_id, url )
    description = _extract_content_with_dsl(
        element, element_id, theme )
    return {
        'description': description,
        'object_name': element_id,
    }


def _cleanup_content(
    content: str,
    cleanup_selectors: __.cabc.Sequence[ str ]
) -> str:
    ''' Removes unwanted elements from content using CSS selectors. '''
    if not content.strip( ) or not cleanup_selectors:
        return content
    soup: __.typx.Any = _BeautifulSoup( content, 'lxml' )
    for selector in cleanup_selectors:
        for element in soup.select( selector ):
            element.decompose( )
    return str( soup )


def _extract_content_with_dsl(
    element: __.typx.Any,
    element_id: str,
    theme: __.Absential[ str ] = __.absent
) -> str:
    ''' Extracts content using universal pattern configuration. '''
    if element.name == 'dt' and _is_api_signature( element ):
        return _extract_api_signature_content( element )
    description = _generic_extraction( element )
    cleanup_selectors = _UNIVERSAL_PATTERNS[ 'navigation_cleanup' ][
        'universal_selectors'
    ]
    return _cleanup_content( description, cleanup_selectors )


def _extract_description_with_strategy(
    element: __.typx.Any,
    strategy: __.cabc.Mapping[ str, __.typx.Any ]
) -> str:
    ''' Extracts description using DSL strategy. '''
    source_type = strategy[ 'description_source' ]
    element_type = strategy.get( 'description_element', 'p' )
    return _get_description_by_source_type(
        element, source_type, element_type )


async def _extract_object_documentation(
    auxdata: __.ApplicationGlobals,
    base_url: __.typx.Any,
    location: str,
    obj: __.InventoryObject,
    theme: __.Absential[ str ] = __.absent,
) -> __.ContentDocument | None:
    ''' Extracts documentation for a single object. '''
    from . import conversion as _conversion
    doc_url = _urls.derive_documentation_url(
        base_url, obj.uri, obj.name )
    try:
        html_content = (
            await __.retrieve_url_as_text(
                auxdata.content_cache, doc_url ) )
    except Exception as exc:
        _scribe.debug( "Failed to retrieve %s: %s", doc_url, exc )
        return None
    anchor = doc_url.fragment or str( obj.name )
    try:
        parsed_content = parse_documentation_html(
            html_content, anchor, str( doc_url ), theme = theme )
    except Exception: return None
    description = _conversion.html_to_markdown(
        parsed_content[ 'description' ] )
    content_id = __.produce_content_id( location, obj.name )
    return __.ContentDocument(
        inventory_object = obj,
        content_id = content_id,
        description = description,
        documentation_url = doc_url.geturl( ),
        extraction_metadata = __.immut.Dictionary( {
            'theme': theme if not __.is_absent( theme ) else 'unknown',
            'extraction_method': 'sphinx_html_parsing',
            'relevance_score': 1.0,
            'match_reasons': [ 'direct extraction' ],
        } )
    )




def _find_main_content_container(
    soup: __.typx.Any, theme: __.Absential[ str ] = __.absent
) -> __.Absential[ __.typx.Any ]:
    ''' Finds main content container trying theme-specific patterns first. '''
    if (
        not __.is_absent( theme )
        and theme in _THEME_PATTERNS[ 'content_containers' ]
    ):
        theme_selectors = _THEME_PATTERNS[ 'content_containers' ][
            theme
        ]
        for selector in theme_selectors:
            container = soup.select_one( selector )
            if container: return container
    content_config = _UNIVERSAL_PATTERNS[ 'content_containers' ]
    universal_selectors = content_config[ 'universal_selectors' ]
    for selector in universal_selectors:
        container = soup.select_one( selector )
        if container: return container
    return __.absent




def _generic_extraction( element: __.typx.Any ) -> str:
    ''' Generic fallback extraction for unknown element types. '''
    description = ''
    if element.parent:
        next_p = element.parent.find( 'p' )
        if next_p:
            description = str( next_p )
    return description


def _get_description_by_source_type(
    element: __.typx.Any,
    source_type: str,
    element_type: str
) -> str:
    ''' Gets description content based on source type. '''
    extractors = {
        'next_sibling': lambda: _get_sibling_text( element, element_type ),
        'parent_next_sibling': lambda: _get_parent_sibling_text(
            element, element_type ),
        'parent_next_element': lambda: _get_parent_element_text(
            element, element_type ),
        'parent_content': lambda: _get_parent_content_text(
            element, element_type ),
        'first_paragraph': lambda: _get_first_paragraph_text( element ),
        'first_main_paragraph': lambda: _get_first_main_paragraph_text(
            element ),
    }
    extractor = extractors.get( source_type )
    return extractor( ) if extractor else ''


def _get_first_paragraph_text( element: __.typx.Any ) -> str:
    ''' Gets HTML content from first paragraph within element. '''
    paragraph = element.find( 'p' )
    return str( paragraph ) if paragraph else ''


def _get_first_main_paragraph_text( element: __.typx.Any ) -> str:
    ''' Gets HTML content from first paragraph, skipping sidebars. '''
    for paragraph in element.find_all( 'p' ):
        if paragraph.find_parent( [ 'aside', 'nav', 'header' ] ):
            continue
        return str( paragraph ) if paragraph else ''
    return ''


def _get_parent_content_text( element: __.typx.Any, element_type: str ) -> str:
    ''' Gets HTML content from content element within parent. '''
    if element.parent:
        content_elem = element.parent.find( element_type )
        return content_elem.decode_contents( ) if content_elem else ''
    return ''


def _get_parent_element_text( element: __.typx.Any, element_type: str ) -> str:
    ''' Gets HTML content from element within parent. '''
    if element.parent:
        next_elem = element.parent.find( element_type )
        return next_elem.decode_contents( ) if next_elem else ''
    return ''


def _get_parent_sibling_text( element: __.typx.Any, element_type: str ) -> str:
    ''' Gets HTML content from parent's next sibling element. '''
    if element.parent:
        sibling = element.parent.find_next_sibling( element_type )
        return sibling.decode_contents( ) if sibling else ''
    return ''


def _get_sibling_text( element: __.typx.Any, element_type: str ) -> str:
    ''' Gets HTML content from next sibling element. '''
    sibling = element.find_next_sibling( element_type )
    return sibling.decode_contents( ) if sibling else ''


def _is_api_signature( element: __.typx.Any ) -> bool:
    ''' Determines if element is an API signature using universal patterns. '''
    signature_config = _UNIVERSAL_PATTERNS[ 'api_signatures' ]
    signature_classes = signature_config[ 'signature_classes' ]
    element_classes = element.get( 'class', [ ] )
    return any( cls in element_classes for cls in signature_classes )


def _extract_api_signature_content( element: __.typx.Any ) -> str:
    ''' Extracts API signature content using universal patterns. '''
    signature_config = _UNIVERSAL_PATTERNS[ 'api_signatures' ]
    description_selector = signature_config[ 'description_selector' ]
    sibling = element.find_next_sibling( description_selector )
    return sibling.decode_contents( ) if sibling else ''
