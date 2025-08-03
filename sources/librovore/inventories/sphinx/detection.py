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


''' Inventory detection implementations. '''


from . import __


class SphinxInventoryDetection( __.InventoryDetection ):
    ''' Detection result for Sphinx inventory sources. '''

    @classmethod
    async def from_source(
        selfclass, processor: __.Processor, source: str
    ) -> __.typx.Self:
        ''' Constructs Sphinx inventory detection from source. '''
        # This is not used in current implementation
        return selfclass( processor = processor, confidence = 0.0 )

    async def filter_inventory(
        self, source: str, /, *,
        filters: __.cabc.Mapping[ str, __.typx.Any ],
        details: __.InventoryQueryDetails = (
            __.InventoryQueryDetails.Documentation ),
    ) -> list[ dict[ str, __.typx.Any ] ]:
        ''' Filters inventory objects from Sphinx source. '''
        from .main import SphinxInventoryProcessor
        processor = __.typx.cast(
            SphinxInventoryProcessor, self.processor )
        return await processor.filter_inventory(
            source, filters = filters, details = details )
