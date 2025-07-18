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


''' Sphinx documentation source detector and processor. '''


import urllib.parse as _urlparse
import httpx as _httpx
import http as _http

from . import __
from .. import functions as _functions
from .. import interfaces as _interfaces
from .. import exceptions as _exceptions


class SphinxProcessor( _interfaces.Processor ):
    ''' Processor for Sphinx documentation sources. '''
    
    name: str = 'sphinx'
    ''' Detector for Sphinx documentation sources. '''

    async def detect( self, source: str ) -> _interfaces.Detection:
        ''' Detect if can process documentation from source. '''
        # Normalize source to get base URL
        try:
            normalized_source = _functions.normalize_inventory_source(
                source
            )
        except Exception:
            return SphinxDetection(
                processor = self, confidence = 0.0, source = source
            )

        # Check for objects.inv
        has_objects_inv = await self._check_objects_inv( normalized_source )
        if not has_objects_inv:
            return SphinxDetection(
                processor = self, confidence = 0.0, source = source
            )

        # Check for searchindex.js (indicates full Sphinx site)
        has_searchindex = await self._check_searchindex( normalized_source )

        # Calculate confidence based on what we found
        confidence = 0.95 if has_searchindex else 0.7
            
        # Build metadata
        metadata: dict[ str, __.typx.Any ] = {
            'has_objects_inv': has_objects_inv,
            'has_searchindex': has_searchindex,
            'normalized_source': normalized_source.geturl( ),
        }
        
        # Try to detect theme and other metadata
        if has_searchindex:
            try:
                theme_metadata = await self._detect_theme( normalized_source )
                metadata.update( theme_metadata )
            except Exception as exc:
                metadata[ 'theme_error' ] = str( exc )
        
        return SphinxDetection(
            processor = self,
            confidence = confidence,
            source = source,
            metadata = metadata
        )

    async def _check_objects_inv(
        self, normalized_source: _urlparse.ParseResult
    ) -> bool:
        ''' Check if objects.inv exists at the source. '''
        try:
            if normalized_source.scheme in ( 'file', '' ):
                # Local file system
                objects_inv_path = __.Path( normalized_source.path )
                return objects_inv_path.exists( )
            # HTTP/HTTPS - try to fetch with HEAD request
            async with _httpx.AsyncClient( timeout = 10.0 ) as client:
                response = await client.head( normalized_source.geturl( ) )
                return response.status_code == _http.HTTPStatus.OK
        except Exception:
            return False

    async def _check_searchindex(
        self, normalized_source: _urlparse.ParseResult
    ) -> bool:
        ''' Check if searchindex.js exists (indicates full Sphinx site). '''
        try:
            # Build searchindex.js URL from objects.inv URL
            searchindex_url = self._build_searchindex_url( normalized_source )

            if searchindex_url.scheme in ( 'file', '' ):
                # Local file system
                searchindex_path = __.Path( searchindex_url.path )
                return searchindex_path.exists( )
            # HTTP/HTTPS - try to fetch with HEAD request
            async with _httpx.AsyncClient( timeout = 10.0 ) as client:
                response = await client.head( searchindex_url.geturl( ) )
                return response.status_code == _http.HTTPStatus.OK
        except Exception:
            return False

    def _build_searchindex_url(
        self, normalized_source: _urlparse.ParseResult
    ) -> _urlparse.ParseResult:
        ''' Build searchindex.js URL from objects.inv URL. '''
        # Remove 'objects.inv' from path and add 'searchindex.js'
        path = normalized_source.path
        if path.endswith( '/objects.inv' ):
            base_path = path[ :-12 ]  # Remove '/objects.inv'
        elif path.endswith( 'objects.inv' ):
            base_path = path[ :-11 ]  # Remove 'objects.inv'
        else:
            base_path = path

        # Add searchindex.js
        # Normalize base_path by ensuring it ends with '/'
        normalized_base = base_path.rstrip( '/' ) + '/'
        searchindex_path = normalized_base + 'searchindex.js'

        return normalized_source._replace( path=searchindex_path )

    async def _detect_theme(
        self, normalized_source: _urlparse.ParseResult
    ) -> dict[ str, __.typx.Any ]:
        ''' Detect Sphinx theme and other metadata. '''
        theme_metadata: dict[ str, __.typx.Any ] = { }

        try:
            # Try to fetch the main HTML page to detect theme
            html_url = self._build_html_url( normalized_source )

            async with _httpx.AsyncClient( timeout = 10.0 ) as client:
                response = await client.get( html_url.geturl( ) )
                if response.status_code == _http.HTTPStatus.OK:
                    html_content = response.text

                    # Simple theme detection based on HTML content
                    if 'furo' in html_content.lower( ):
                        theme_metadata[ 'theme' ] = 'furo'
                    elif 'alabaster' in html_content.lower( ):
                        theme_metadata[ 'theme' ] = 'alabaster'
                    elif 'sphinx_rtd_theme' in html_content.lower( ):
                        theme_metadata[ 'theme' ] = 'sphinx_rtd_theme'
                    else:
                        theme_metadata[ 'theme' ] = 'unknown'

        except Exception:
            theme_metadata[ 'theme' ] = 'unknown'

        return theme_metadata

    def _build_html_url(
        self, normalized_source: _urlparse.ParseResult
    ) -> _urlparse.ParseResult:
        ''' Build main HTML URL from objects.inv URL. '''
        # Remove 'objects.inv' from path and add 'index.html'
        path = normalized_source.path
        if path.endswith( '/objects.inv' ):
            base_path = path[ :-12 ]  # Remove '/objects.inv'
        elif path.endswith( 'objects.inv' ):
            base_path = path[ :-11 ]  # Remove 'objects.inv'
        else:
            base_path = path

        # Add index.html
        # Normalize base_path by ensuring it ends with '/'
        normalized_base = base_path.rstrip( '/' ) + '/'
        html_path = normalized_base + 'index.html'

        return normalized_source._replace( path=html_path )


class SphinxDetection( _interfaces.Detection ):
    ''' Detection result for Sphinx documentation sources. '''
    
    source: str
    metadata: dict[ str, __.typx.Any ] = __.dcls.field( 
        default_factory=lambda: __.typx.cast( dict[ str, __.typx.Any ], { } )
    )
    
    @classmethod
    async def from_source(
        cls, processor: _interfaces.Processor, source: str
    ) -> __.typx.Self:
        ''' Constructs detection from source location. '''
        if not isinstance( processor, SphinxProcessor ):
            raise _exceptions.ProcessorTypeError(
                "SphinxProcessor", type( processor )
            )
        detection = await processor.detect( source )
        return __.typx.cast( __.typx.Self, detection )
    
    @property
    def specifics( self ) -> _interfaces.DetectionSpecifics:
        ''' Returns metadata associated with detection as dictionary. '''
        return {
            'source': self.source,
            'processor_name': self.processor.name,
            **self.metadata
        }


# Global processor instance
_sphinx_processor = SphinxProcessor( )


def register( ) -> None:
    ''' Register the Sphinx processor with the processors registry. '''
    from .. import xtnsapi as _xtnsapi
    _xtnsapi.processors[ _sphinx_processor.name ] = _sphinx_processor


def get_processor( ) -> SphinxProcessor:
    ''' Get the Sphinx processor instance. '''
    return _sphinx_processor
