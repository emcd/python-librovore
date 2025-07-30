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


''' Sphinx detection and metadata extraction. '''


from urllib.parse import ParseResult as _Url

from . import __
from . import urls as _urls


_scribe = __.acquire_scribe( __name__ )


class SphinxDetection( __.Detection ):
    ''' Detection result for Sphinx documentation sources. '''

    source: str
    has_objects_inv: bool = False
    has_searchindex: bool = False
    normalized_source: str = ''
    theme: __.typx.Optional[ str ] = None

    @classmethod
    async def from_source(
        cls, processor: __.Processor, source: str
    ) -> __.typx.Self:
        ''' Constructs detection from source location. '''
        from .main import SphinxProcessor as _SphinxProcessor
        if not isinstance( processor, _SphinxProcessor ):
            raise __.ProcessorInvalidity(
                "SphinxProcessor", type( processor ) )
        detection = await processor.detect( source )
        return __.typx.cast( __.typx.Self, detection )

    async def extract_documentation_for_objects(
        self, source: str,
        objects: __.cabc.Sequence[ __.cabc.Mapping[ str, __.typx.Any ] ], /, *,
        include_snippets: bool = True,
    ) -> list[ dict[ str, __.typx.Any ] ]:
        ''' Extracts documentation content for specified objects. '''
        from . import extraction as _extraction
        theme = self.theme if self.theme is not None else __.absent
        return await _extraction.extract_documentation_for_objects(
            source, objects, 
            theme = theme,
            include_snippets = include_snippets
        )
    
    async def extract_filtered_inventory(
        self, source: str, /, *,
        filters: __.cabc.Mapping[ str, __.typx.Any ],
        details: __.InventoryQueryDetails = (
            __.InventoryQueryDetails.Documentation ),
    ) -> list[ dict[ str, __.typx.Any ] ]:
        ''' Extracts and filters inventory objects from source. '''
        from . import inventory as _inventory
        return await _inventory.extract_filtered_inventory(
            source, filters = filters, details = details )


async def check_objects_inv( source: _Url ) -> bool:
    ''' Checks if objects.inv exists at the source. '''
    inventory_url = _urls.derive_inventory_url( source )
    return await __.probe_url( inventory_url )


async def check_searchindex( source: _Url ) -> bool:
    ''' Checks if searchindex.js exists (indicates full Sphinx site). '''
    searchindex_url = _urls.derive_searchindex_url( source )
    return await __.probe_url( searchindex_url )


async def detect_theme( source: _Url ) -> dict[ str, __.typx.Any ]:
    ''' Detects Sphinx theme and other metadata. '''
    from ...cacheproxy import retrieve_url_as_text as _retrieve_url_as_text
    theme_metadata: dict[ str, __.typx.Any ] = { }
    html_url = _urls.derive_html_url( source )
    try: html_content = await _retrieve_url_as_text(
        html_url, duration_max = 10.0 )
    except __.DocumentationInaccessibility: pass
    else:
        html_content_lower = html_content.lower( )
        # Check for theme-specific CSS files and identifiers
        if ( 'furo' in html_content_lower 
             or 'css/furo.css' in html_content_lower ):
            theme_metadata[ 'theme' ] = 'furo'
        elif ( 'sphinx_rtd_theme' in html_content_lower 
               or 'css/theme.css' in html_content_lower ):
            theme_metadata[ 'theme' ] = 'sphinx_rtd_theme'
        elif ( 'alabaster' in html_content_lower 
               or 'css/alabaster.css' in html_content_lower ):
            theme_metadata[ 'theme' ] = 'alabaster'
        elif ( 'pydoctheme.css' in html_content_lower 
               or 'classic.css' in html_content_lower ):
            theme_metadata[ 'theme' ] = 'pydoctheme'  # Python docs theme
        elif 'flask.css' in html_content_lower:
            theme_metadata[ 'theme' ] = 'flask'  # Flask docs theme
        elif 'css/nature.css' in html_content_lower:
            theme_metadata[ 'theme' ] = 'nature'
        elif 'css/default.css' in html_content_lower:
            theme_metadata[ 'theme' ] = 'classic'
        elif 'sphinx_book_theme' in html_content_lower:
            theme_metadata[ 'theme' ] = 'sphinx_book_theme'
        elif 'pydata_sphinx_theme' in html_content_lower:
            theme_metadata[ 'theme' ] = 'pydata_sphinx_theme'
        # If no theme detected, don't set theme key (returns None)
    return theme_metadata


