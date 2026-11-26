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


''' Main Pydoctor processor implementation. '''


from . import __
from . import detection as _detection


_scribe = __.acquire_scribe( __name__ )


class PydoctorProcessor( __.Processor ):
    ''' Processor for Pydoctor documentation sources. '''

    name: str = 'pydoctor'

    @property
    def capabilities( self ) -> __.ProcessorCapabilities:
        ''' Returns Pydoctor processor capabilities. '''
        return __.ProcessorCapabilities(
            processor_name = 'pydoctor',
            version = '1.0.0',
            supported_filters = [ ],
            results_limit_max = 100,
            response_time_typical = 'fast',
            notes = (
                'Works with Pydoctor-generated '
                'Python API documentation sites' ),
        )

    async def detect(
        self, auxdata: __.ApplicationGlobals, source: str
    ) -> __.StructureDetection:
        ''' Detects if can process documentation from source. '''
        try:
            base_url = __.normalize_base_url( source )
        except Exception:
            return _detection.PydoctorDetection(
                processor = self, confidence = 0.0, source = source )
        confidence = await _detection.detect_pydoctor(
            auxdata, base_url )
        return _detection.PydoctorDetection(
            processor = self,
            confidence = confidence,
            source = source,
            normalized_source = base_url.geturl( ) )
