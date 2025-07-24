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


import http as _http

from urllib.parse import ParseResult as _Url

import httpx as _httpx

from . import __


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
        from .core import SphinxProcessor as _SphinxProcessor
        if not isinstance( processor, _SphinxProcessor ):
            raise __.ProcessorTypeError(
                "SphinxProcessor", type( processor ) )
        detection = await processor.detect( source )
        return __.typx.cast( __.typx.Self, detection )


async def check_objects_inv( source: _Url ) -> bool:
    ''' Checks if objects.inv exists at the source. '''
    from .urls import derive_inventory_url as _derive_inventory_url
    inventory_url = _derive_inventory_url( source )
    return await probe_url( inventory_url )


async def check_searchindex( source: _Url ) -> bool:
    ''' Checks if searchindex.js exists (indicates full Sphinx site). '''
    from .urls import derive_searchindex_url as _derive_searchindex_url
    searchindex_url = _derive_searchindex_url( source )
    return await probe_url( searchindex_url )


async def detect_theme( source: _Url ) -> dict[ str, __.typx.Any ]:
    ''' Detects Sphinx theme and other metadata. '''
    from .urls import derive_html_url as _derive_html_url
    from .extraction import retrieve_url as _retrieve_url
    theme_metadata: dict[ str, __.typx.Any ] = { }
    html_url = _derive_html_url( source )
    try: html_content = await _retrieve_url( html_url, timeout = 10.0 )
    except __.DocumentationInaccessibility: pass
    else:
        html_content_lower = html_content.lower( )
        if 'furo' in html_content_lower:
            theme_metadata[ 'theme' ] = 'furo'
        elif 'alabaster' in html_content_lower:
            theme_metadata[ 'theme' ] = 'alabaster'
        elif 'sphinx_rtd_theme' in html_content_lower:
            theme_metadata[ 'theme' ] = 'sphinx_rtd_theme'
        # If no theme detected, don't set theme key (returns None)
    return theme_metadata


async def probe_url( url: _Url, *, timeout: float = 10.0 ) -> bool:
    ''' Checks if URL exists using HEAD request or file existence check. '''
    match url.scheme:
        case 'file' | '':
            file_path = __.Path( url.path )
            return file_path.exists( )
        case 'http' | 'https':
            try:
                async with _httpx.AsyncClient( timeout = timeout ) as client:
                    response = await client.head( url.geturl( ) )
            except Exception: return False
            else: return response.status_code == _http.HTTPStatus.OK
        case _: return False