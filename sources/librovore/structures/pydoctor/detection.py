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


''' Pydoctor detection and metadata extraction. '''


from urllib.parse import ParseResult as _Url

from . import __
from . import extraction as _extraction
from . import urls as _urls


_scribe = __.acquire_scribe( __name__ )


class PydoctorDetection( __.StructureDetection ):
    ''' Detection result for Pydoctor documentation sources. '''

    source: str
    normalized_source: str = ''

    @classmethod
    def get_capabilities( cls ) -> __.StructureProcessorCapabilities:
        ''' Pydoctor processor capabilities. '''
        return __.StructureProcessorCapabilities(
            supported_inventory_types = frozenset( { 'pydoctor' } ),
            content_extraction_features = frozenset( {
                __.ContentExtractionFeatures.Signatures,
                __.ContentExtractionFeatures.Descriptions,
                __.ContentExtractionFeatures.CodeExamples,
            } ),
            confidence_by_inventory_type = __.immut.Dictionary( {
                'pydoctor': 1.0
            } )
        )

    @classmethod
    async def from_source(
        selfclass,
        auxdata: __.ApplicationGlobals,
        processor: __.Processor,
        source: str,
    ) -> __.typx.Self:
        ''' Constructs detection from source location. '''
        detection = await processor.detect( auxdata, source )
        return __.typx.cast( __.typx.Self, detection )

    async def extract_contents(
        self,
        auxdata: __.ApplicationGlobals,
        source: str,
        objects: __.cabc.Sequence[ __.InventoryObject ], /,
    ) -> tuple[ __.ContentDocument, ... ]:
        ''' Extracts documentation content for specified objects. '''
        documents = await _extraction.extract_contents(
            auxdata, source, objects )
        return tuple( documents )


async def detect_pydoctor(
    auxdata: __.ApplicationGlobals, base_url: _Url
) -> float:
    ''' Detects if source is a Pydoctor documentation site. '''
    confidence = 0.0

    # Check for index.html
    index_url = _urls.derive_index_url( base_url )
    try:
        html_content = await __.retrieve_url_as_text(
            auxdata.content_cache,
            index_url, duration_max = 10.0 )
        html_lower = html_content.lower( )

        # Check for pydoctor meta tag (highest confidence)
        if '<meta name="generator" content="pydoctor' in html_lower:
            confidence = 1.0
        # Check for characteristic CSS files
        elif 'apidocs.css' in html_lower:
            confidence = 0.8
        # Check for Bootstrap-based navigation with pydoctor structure
        elif 'navbar navbar-default mainnavbar' in html_lower:
            confidence += 0.3
        # Check for pydoctor-specific elements
        if 'class="docstring"' in html_lower:
            confidence += 0.2

        confidence = min( confidence, 1.0 )
    except Exception as exc:
        _scribe.debug( f"Detection failed for {base_url.geturl( )}: {exc}" )

    return confidence
