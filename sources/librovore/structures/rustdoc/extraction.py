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


''' Documentation extraction and content retrieval for Rustdoc. '''


import urllib.parse as _urlparse

from bs4 import BeautifulSoup as _BeautifulSoup

from . import __
from . import conversion as _conversion


_scribe = __.acquire_scribe( __name__ )


async def extract_contents(
    auxdata: __.ApplicationGlobals,
    source: str,
    objects: __.cabc.Sequence[ __.InventoryObject ], /,
) -> list[ __.ContentDocument ]:
    ''' Extracts documentation content for specified objects. '''
    if not objects: return [ ]
    tasks = [
        extract_object_documentation( auxdata, source, obj )
        for obj in objects ]
    candidate_results = await __.asyncf.gather_async(
        *tasks, return_exceptions = True )
    results: list[ __.ContentDocument ] = [
        result.value for result in candidate_results
        if __.generics.is_value( result ) and result.value is not None ]
    return results


async def extract_object_documentation(
    auxdata: __.ApplicationGlobals,
    source: str,
    obj: __.InventoryObject,
) -> __.Absential[ __.ContentDocument ]:
    ''' Extracts documentation for a single Rustdoc object. '''
    doc_url = _urlparse.urlparse( obj.uri )
    try:
        html_content = await __.retrieve_url_as_text(
            auxdata.content_cache, doc_url, duration_max = 10.0 )
    except __.DocumentationInaccessibility as exc:
        _scribe.warning( f"Cannot retrieve {obj.uri}: {exc}" )
        return __.absent
    if __.is_absent( html_content ):
        _scribe.warning( f"Empty content from {obj.uri}." )
        return __.absent
    try:
        content_parts = parse_documentation_html( html_content, obj.uri )
    except Exception as exc:
        _scribe.warning( f"Parse failure for {obj.uri}: {exc}" )
        return __.absent
    markdown_content = _assemble_markdown_content( obj, content_parts )
    content_id = f"{obj.name}@{obj.uri}"
    return __.ContentDocument(
        inventory_object = obj,
        content_id = content_id,
        description = markdown_content,
        documentation_url = obj.uri,
        extraction_metadata = __.immut.Dictionary( {
            'extraction_method': 'rustdoc_html_parsing',
            'relevance_score': 1.0,
            'match_reasons': [ 'direct extraction' ],
        } )
    )


def parse_documentation_html(
    content: str, url: str
) -> dict[ str, str ]:
    ''' Parses HTML content to extract documentation sections. '''
    try: soup = _BeautifulSoup( content, 'lxml' )
    except Exception as exc:
        raise __.DocumentationParseFailure( url, exc ) from exc
    main_content = soup.find( 'main' )
    if not main_content:
        section_content = soup.find( 'section', id = 'main-content' )
        if not section_content:
            raise __.DocumentationContentAbsence( url )
        main_content = section_content
    cleanup_navigation_elements( main_content )
    item_decl = extract_item_declaration( main_content )
    docblocks = extract_docblocks( main_content )
    code_examples = extract_code_examples( main_content )
    return {
        'item_declaration': item_decl,
        'documentation': docblocks,
        'code_examples': code_examples,
    }


def cleanup_navigation_elements( soup: __.typx.Any ) -> None:
    ''' Removes navigation and UI elements from parsed HTML. '''
    cleanup_selectors = (
        'nav.sidebar',
        'rustdoc-toolbar',
        'rustdoc-topbar',
        '.sidebar-resizer',
        '.src',
        '.out-of-band',
    )
    for selector in cleanup_selectors:
        for element in soup.select( selector ):
            element.decompose( )


def extract_code_examples( soup: __.typx.Any ) -> str:
    ''' Extracts code examples from documentation. '''
    examples: list[ str ] = [ ]
    example_wraps = soup.find_all( 'div', class_ = 'example-wrap' )
    for wrap in example_wraps:
        code_block = wrap.find( 'pre', class_ = 'rust' )
        if code_block:
            code_text = code_block.get_text( strip = True )
            if code_text:
                examples.append( f"```rust\n{code_text}\n```" )
    return '\n\n'.join( examples )


def extract_docblocks( soup: __.typx.Any ) -> str:
    ''' Extracts documentation blocks from main content. '''
    docblocks = soup.find_all( 'div', class_ = 'docblock' )
    if not docblocks: return ''
    parts: list[ str ] = [ ]
    for docblock in docblocks:
        _remove_nested_code_examples( docblock )
        html_str = str( docblock )
        markdown = _conversion.convert_to_markdown( html_str )
        if markdown:
            parts.append( markdown )
    return '\n\n'.join( parts )


def extract_item_declaration( soup: __.typx.Any ) -> str:
    ''' Extracts item type declaration from documentation. '''
    item_decl = soup.find( 'pre', class_ = 'rust item-decl' )
    if not item_decl: return ''
    decl_text = item_decl.get_text( strip = True )
    if decl_text:
        return f"```rust\n{decl_text}\n```"
    return ''


def _assemble_markdown_content(
    obj: __.InventoryObject, parts: dict[ str, str ]
) -> str:
    ''' Assembles final Markdown content from extracted parts. '''
    sections: list[ str ] = [ ]
    if parts.get( 'item_declaration' ):
        sections.append( f"## Declaration\n\n{parts['item_declaration']}" )
    if parts.get( 'documentation' ):
        sections.append( f"## Documentation\n\n{parts['documentation']}" )
    if parts.get( 'code_examples' ):
        sections.append( f"## Examples\n\n{parts['code_examples']}" )
    if not sections:
        return f"# {obj.display_name}\n\nNo documentation available."
    return f"# {obj.display_name}\n\n" + '\n\n'.join( sections )


def _remove_nested_code_examples( docblock: __.typx.Any ) -> None:
    ''' Removes nested code examples to avoid duplication. '''
    for example_wrap in docblock.find_all( 'div', class_ = 'example-wrap' ):
        example_wrap.decompose( )
