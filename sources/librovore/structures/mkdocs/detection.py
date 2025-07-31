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


''' MkDocs detection and metadata extraction. '''


from urllib.parse import ParseResult as _Url

from . import __
from ...inventories import sphinx as _sphinx_inventory


_scribe = __.acquire_scribe( __name__ )


class MkDocsDetection( __.Detection ):
    ''' Detection result for MkDocs documentation sources. '''

    source: str
    has_objects_inv: bool = False
    has_mkdocs_yml: bool = False
    normalized_source: str = ''
    theme: __.typx.Optional[ str ] = None

    @classmethod
    async def from_source(
        cls, processor: __.Processor, source: str
    ) -> __.typx.Self:
        ''' Constructs detection from source location. '''
        # Note: This method is used by the protocol but actual construction
        # happens in the processor's detect method to avoid circular imports
        if processor.name != 'mkdocs':
            raise __.ProcessorInvalidity(
                "MkDocsProcessor", type( processor ) )
        detection = await processor.detect( source )
        return __.typx.cast( __.typx.Self, detection )

    async def extract_contents(
        self, source: str,
        objects: __.cabc.Sequence[ __.cabc.Mapping[ str, __.typx.Any ] ], /, *,
        include_snippets: bool = True,
    ) -> list[ dict[ str, __.typx.Any ] ]:
        ''' Extracts documentation content for specified objects. '''
        # For v1.0, delegate to Sphinx inventory extraction since
        # mkdocstrings generates Sphinx inventories
        return [ ]  # TODO: Implement MkDocs-specific content extraction

    async def filter_inventory(
        self, source: str, /, *,
        filters: __.cabc.Mapping[ str, __.typx.Any ],
        details: __.InventoryQueryDetails = (
            __.InventoryQueryDetails.Documentation ),
    ) -> list[ dict[ str, __.typx.Any ] ]:
        ''' Extracts and filters inventory objects from source. '''
        return await _sphinx_inventory.filter_inventory(
            source, filters = filters, details = details )


async def check_objects_inv( source: _Url ) -> bool:
    ''' Checks if objects.inv exists at the source. '''
    from ..sphinx.urls import derive_inventory_url as _derive_inventory_url
    inventory_url = _derive_inventory_url( source )
    return await __.probe_url( inventory_url )


async def check_mkdocs_yml( source: _Url ) -> bool:
    ''' Checks if mkdocs.yml exists (indicates MkDocs site). '''
    mkdocs_url = source._replace( path = f"{source.path}/mkdocs.yml" )
    return await __.probe_url( mkdocs_url )


async def detect_theme( source: _Url ) -> dict[ str, __.typx.Any ]:
    ''' Detects MkDocs theme and other metadata. '''
    from ...cacheproxy import retrieve_url_as_text as _retrieve_url_as_text
    theme_metadata: dict[ str, __.typx.Any ] = { }
    
    # Try multiple common HTML file locations
    html_candidates = [
        source._replace( path = f"{source.path}/" ),  # Base URL (redirects)
        source._replace( path = f"{source.path}/index.html" ),
    ]
    
    html_content = None
    for html_url in html_candidates:
        try: 
            html_content = await _retrieve_url_as_text(
                html_url, duration_max = 10.0 )
            break
        except __.DocumentationInaccessibility: 
            continue
    
    if html_content:
        html_content_lower = html_content.lower( )
        # Check for Material for MkDocs theme
        if ( 'material' in html_content_lower
             or 'mkdocs-material' in html_content_lower ):
            theme_metadata[ 'theme' ] = 'material'
        elif 'readthedocs' in html_content_lower:
            theme_metadata[ 'theme' ] = 'readthedocs'
        # If no theme detected, don't set theme key (returns None)
    return theme_metadata