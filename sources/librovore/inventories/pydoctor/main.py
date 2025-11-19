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


''' Pydoctor inventory processor for searchindex.json format. '''

from . import __
from . import detection as _detection


class PydoctorInventoryProcessor( __.Processor ):
    ''' Processes Pydoctor inventory files (searchindex.json format). '''

    name: str = 'pydoctor'

    @property
    def capabilities( self ) -> __.ProcessorCapabilities:
        ''' Returns Pydoctor inventory processor capabilities. '''
        return __.ProcessorCapabilities(
            processor_name = 'pydoctor',
            version = '1.0.0',
            supported_filters = [
                __.FilterCapability(
                    name = 'type',
                    description = (
                        'Filter by object type (module, class, function)' ),
                    type = 'string'
                ),
            ],
            results_limit_max = 10000,
            response_time_typical = 'fast',
            notes = (
                'Processes Pydoctor searchindex.json files from '
                'Python API documentation' )
        )

    async def detect(
        self, auxdata: __.ApplicationGlobals, source: str
    ) -> __.InventoryDetection:
        ''' Detects if source has a Pydoctor searchindex.json file. '''
        base_url = __.normalize_base_url( source )
        has_searchindex = await _detection.check_searchindex(
            auxdata, base_url )
        if has_searchindex:
            return _detection.PydoctorInventoryDetection(
                processor = self, confidence = 1.0 )
        return _detection.PydoctorInventoryDetection(
            processor = self, confidence = 0.0 )
