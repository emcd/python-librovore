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


''' Rustdoc inventory processor for all items page format. '''

from . import __
from . import detection as _detection


class RustdocInventoryProcessor( __.Processor ):
    ''' Processes Rustdoc all items pages (all.html format). '''

    name: str = 'rustdoc'

    @property
    def capabilities( self ) -> __.ProcessorCapabilities:
        ''' Returns Rustdoc inventory processor capabilities. '''
        return __.ProcessorCapabilities(
            processor_name = 'rustdoc',
            version = '1.0.0',
            supported_filters = [
                __.FilterCapability(
                    name = 'item_type',
                    description = (
                        'Filter by Rust item type '
                        '(struct, enum, trait, fn, macro, mod, const, etc.)' ),
                    type = 'string'
                ),
                __.FilterCapability(
                    name = 'name',
                    description = 'Filter by item name pattern',
                    type = 'string'
                ),
            ],
            results_limit_max = 10000,
            response_time_typical = 'fast',
            notes = 'Processes Rustdoc all items pages (all.html format)'
        )

    async def detect(
        self, auxdata: __.ApplicationGlobals, source: str
    ) -> __.InventoryDetection:
        ''' Detects if source has a Rustdoc all items page. '''
        return await _detection.RustdocInventoryDetection.from_source(
            auxdata, self, source )
