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


''' Main Rustdoc structure processor implementation. '''


from . import __
from . import detection as _detection


_scribe = __.acquire_scribe( __name__ )


class RustdocStructureProcessor( __.Processor ):
    ''' Processor for Rustdoc documentation structure. '''

    name: str = 'rustdoc'

    @property
    def capabilities( self ) -> __.ProcessorCapabilities:
        ''' Returns Rustdoc processor capabilities. '''
        return __.ProcessorCapabilities(
            processor_name = 'rustdoc',
            version = '1.0.0',
            supported_filters = [
                __.FilterCapability(
                    name = 'item_type',
                    description = (
                        'Rustdoc item type (struct, enum, trait, fn)' ),
                    type = 'string',
                    values = None,
                ),
            ],
            results_limit_max = 100,
            response_time_typical = 'fast',
            notes = 'Works with Rustdoc-generated documentation sites',
        )

    async def detect(
        self, auxdata: __.ApplicationGlobals, source: str
    ) -> __.StructureDetection:
        ''' Detects if can process documentation from source. '''
        try: base_url = __.normalize_base_url( source )
        except Exception:
            return _detection.RustdocDetection(
                processor = self, confidence = 0.0, source = source )
        normalized_url = base_url.geturl( )
        is_rustdoc, rustdoc_version = await _detection.detect_rustdoc(
            auxdata, base_url )
        confidence = 0.95 if is_rustdoc else 0.0
        return _detection.RustdocDetection(
            processor = self,
            confidence = confidence,
            source = source,
            normalized_source = normalized_url,
            rustdoc_version = rustdoc_version )
