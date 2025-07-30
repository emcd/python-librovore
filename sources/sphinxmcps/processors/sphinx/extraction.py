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


async def extract_contents(
    source: str,
    objects: __.cabc.Sequence[ __.cabc.Mapping[ str, __.typx.Any ] ], /, *,
    theme: __.Absential[ str ] = __.absent,
    include_snippets: bool = True,
) -> list[ dict[ str, __.typx.Any ] ]:
    ''' Extracts documentation content for specified objects. '''
    base_url = _urls.normalize_base_url( source )
    if not objects: return [ ]
    tasks = [
        _extract_object_documentation(
            base_url, dict( obj ), include_snippets, theme )
        for obj in objects ]
    candidate_results = await __.asyncf.gather_async(
        *tasks, return_exceptions = True )
    results: list[ dict[ str, __.typx.Any ] ] = [
        dict( result.value ) for result in candidate_results
        if __.generics.is_value( result ) and result.value is not None ]
    return results


def parse_documentation_html(
    content: str, element_id: str, *, theme: __.Absential[ str ] = __.absent
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
        return { 'error': f"Object '{element_id}' not found in page" }
    if element.name == 'dt':
        signature, description = _extract_dt_content( element )
    elif element.name == 'section':
        signature, description = _extract_section_content( element )
    else:
        signature = element.get_text( strip = True )
        description = ''
    return {
        'signature': signature,
        'description': description,
        'object_name': element_id,
    }


def _extract_dt_content( element: __.typx.Any ) -> tuple[ str, str ]:
    ''' Extracts signature and description from dt/dd elements. '''
    signature = element.get_text( strip = True )
    description_element = element.find_next_sibling( 'dd' )
    if description_element:
        for header_link in description_element.find_all(
            'a', class_ = 'headerlink'
        ): header_link.decompose( )
        description = description_element.get_text( strip = True )
    else: description = ''
    return signature, description


async def _extract_object_documentation(
    base_url: __.typx.Any,
    obj: dict[ str, __.typx.Any ],
    include_snippets: bool,
    theme: __.Absential[ str ] = __.absent
) -> dict[ str, __.typx.Any ] | None:
    ''' Extracts documentation for a single object. '''
    from . import conversion as _conversion
    doc_url = _urls.derive_documentation_url(
        base_url, obj[ 'uri' ], obj[ 'name' ] )
    try: html_content = await __.retrieve_url_as_text( doc_url )
    except Exception as exc:
        __.acquire_scribe( __name__ ).debug(
            "Failed to retrieve %s: %s", doc_url, exc )
        return None
    anchor = doc_url.fragment or str( obj[ 'name' ] )
    try:
        parsed_content = parse_documentation_html(
            html_content, anchor, theme = theme )
    except Exception: return None
    if 'error' in parsed_content: return None
    description = _conversion.html_to_markdown(
        parsed_content[ 'description' ] )
    snippet_max_length = 200
    if include_snippets:
        content_snippet = (
            description[ : snippet_max_length ] + '...'
            if len( description ) > snippet_max_length
            else description )
    else: content_snippet = ''
    return {
        'object_name': obj[ 'name' ],
        'object_type': obj[ 'role' ],
        'domain': obj[ 'domain' ],
        'priority': obj[ 'priority' ],
        'url': doc_url.geturl( ),
        'signature': parsed_content[ 'signature' ],
        'description': description,
        'content_snippet': content_snippet,
        'relevance_score': 1.0,
        'match_reasons': [ 'direct extraction' ],
    }


def _extract_section_content(
    element: __.typx.Any
) -> tuple[ str, str ]:
    ''' Extracts signature and description from section elements. '''
    header = element.find( [ 'h1', 'h2', 'h3', 'h4', 'h5', 'h6' ] )
    signature = header.get_text( strip = True ) if header else ''
    description_element = element.find( 'p' )
    if description_element:
        description = description_element.get_text( strip = True )
    else: description = ''
    return signature, description


def _find_main_content_container(
    soup: __.typx.Any, theme: __.Absential[ str ] = __.absent
) -> __.Absential[ __.typx.Any ]:
    ''' Finds the main content container using theme-specific strategies. '''
    if theme == 'furo':
        containers = [
            soup.find( 'article', { 'role': 'main' } ),
            soup.find( 'div', { 'id': 'furo-main-content' } ),
        ]
    elif theme == 'sphinx_rtd_theme':
        containers = [
            soup.find( 'div', { 'class': 'document' } ),
            soup.find( 'div', { 'class': 'body' } ),
            soup.find( 'div', { 'role': 'main' } ),
        ]
    elif theme == 'pydoctheme':  # Python docs
        containers = [
            soup.find( 'div', { 'class': 'body' } ),
            soup.find( 'div', { 'class': 'content' } ),
            soup.body,  # Python docs often use body directly
        ]
    elif theme == 'flask':  # Flask docs
        containers = [
            soup.find( 'div', { 'class': 'body' } ),
            soup.find( 'div', { 'class': 'content' } ),
            soup.body,
        ]
    elif theme == 'alabaster':
        containers = [
            soup.find( 'div', { 'class': 'body' } ),
            soup.find( 'div', { 'class': 'content' } ),
        ]
    else:  # Generic fallback for unknown themes
        containers = [
            soup.find( 'article', { 'role': 'main' } ),  # Furo theme
            soup.find( 'div', { 'class': 'body' } ),  # Basic theme
            soup.find( 'div', { 'class': 'content' } ),  # Nature theme
            soup.find( 'div', { 'class': 'main' } ),  # Generic main
            soup.find( 'main' ),  # HTML5 main element
            soup.find( 'div', { 'role': 'main' } ),  # Role-based
            soup.body,  # Fallback to body if nothing else works
        ]
    for container in containers:
        if container: return container
    return __.absent
