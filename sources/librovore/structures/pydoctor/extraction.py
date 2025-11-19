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
from . import conversion as _conversion
from . import urls as _urls


_scribe = __.acquire_scribe( __name__ )


async def extract_contents(
    auxdata: __.ApplicationGlobals,
    source: str,
    objects: __.cabc.Sequence[ __.InventoryObject ], /,
) -> list[ __.ContentDocument ]:
    ''' Extracts documentation content for specified objects. '''
    if not objects: return [ ]
    tasks = [
        _extract_object_documentation( auxdata, source, obj )
        for obj in objects ]
    candidate_results = await __.asyncf.gather_async(
        *tasks, return_exceptions = True )
    results: list[ __.ContentDocument ] = [
        result.value for result in candidate_results
        if __.generics.is_value( result ) and result.value is not None ]
    return results


def parse_pydoctor_html(
    content: str, qname: str
) -> __.cabc.Mapping[ str, str ]:
    ''' Parses Pydoctor HTML to extract documentation. '''
    try: soup = _BeautifulSoup( content, 'lxml' )
    except Exception as exc:
        raise __.DocumentationParseFailure( qname, exc ) from exc

    # Extract signature from various possible locations
    signature = _extract_signature( soup, qname )

    # Extract docstring content
    docstring = _extract_docstring( soup )

    description_parts: list[ str ] = [ ]
    if signature:
        description_parts.append( f"```python\n{signature}\n```" )
    if docstring:
        description_parts.append( docstring )

    return {
        'description': '\n\n'.join( description_parts ),
        'object_name': qname,
    }


async def _extract_object_documentation(
    auxdata: __.ApplicationGlobals,
    location: str,
    obj: __.InventoryObject,
) -> __.ContentDocument | None:
    ''' Extracts documentation for a single object. '''
    base_url = _urls.normalize_base_url( location )
    doc_url = _urls.derive_documentation_url( base_url, obj.uri )

    try:
        html_content = await __.retrieve_url_as_text(
            auxdata.content_cache, doc_url )
    except Exception as exc:
        _scribe.debug( "Failed to retrieve %s: %s", doc_url, exc )
        return None

    try:
        parsed_content = parse_pydoctor_html( html_content, obj.name )
    except Exception as exc:
        _scribe.debug( "Failed to parse %s: %s", obj.name, exc )
        return None

    description = _conversion.html_to_markdown(
        parsed_content[ 'description' ] )
    content_id = __.produce_content_id( location, obj.name )

    return __.ContentDocument(
        inventory_object = obj,
        content_id = content_id,
        description = description,
        documentation_url = doc_url.geturl( ) )


def _extract_docstring( soup: __.typx.Any ) -> str:
    ''' Extracts docstring from .docstring div. '''
    docstring_div = soup.find( 'div', class_ = 'docstring' )
    if not docstring_div: return ''

    # Remove navigation elements
    for nav in docstring_div.find_all( 'nav' ):
        nav.decompose( )

    return str( docstring_div )


def _extract_signature( soup: __.typx.Any, qname: str ) -> str:
    ''' Extracts signature from Pydoctor HTML. '''
    # Try to find the signature in various locations

    # 1. Look for thisobject in thingTitle (module/class name)
    thisobject = soup.find( 'code', class_ = 'thisobject' )
    if thisobject:
        signature_text = thisobject.get_text( strip = True )
        if signature_text:
            return signature_text

    # 2. Look for function header
    function_header = soup.find( 'div', class_ = 'functionHeader' )
    if function_header:
        code = function_header.find( 'code' )
        if code:
            signature_text = code.get_text( strip = True )
            if signature_text:
                return signature_text

    # 3. Look for code in thingTitle
    thing_title = soup.find( class_ = 'thingTitle' )
    if thing_title:
        code = thing_title.find( 'code' )
        if code:
            signature_text = code.get_text( strip = True )
            if signature_text:
                return signature_text

    # 4. Fallback to qualified name
    return qname
