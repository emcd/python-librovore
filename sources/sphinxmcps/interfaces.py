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


''' Common enumerations and interfaces. '''


from . import __
from . import exceptions as _exceptions


class FilterCapability( __.immut.DataclassObject ):
    ''' Describes a filter supported by a processor. '''

    name: str
    description: str
    type: str  # "string", "enum", "boolean"
    values: __.typx.Optional[ list[ str ] ] = None  # For enums
    required: bool = False


class InventoryQueryDetails( __.enum.IntFlag ):
    ''' Enumeration for inventory query detail levels. '''

    Name =          0               # Object names only (baseline)
    Signature =     __.enum.auto( ) # Include signatures
    Summary =       __.enum.auto( ) # Include brief descriptions
    Documentation = __.enum.auto( ) # Include full documentation


class MatchMode( str, __.enum.Enum ):
    ''' Enumeration for different term matching modes. '''

    Exact = 'exact'
    Regex = 'regex'
    Fuzzy = 'fuzzy'


class SearchBehaviors( __.immut.DataclassObject ):
    ''' Search behavior configuration for the search engine. '''

    match_mode: MatchMode = MatchMode.Fuzzy
    fuzzy_threshold: int = 50


_search_behaviors_default = SearchBehaviors( )
_filters_default = __.immut.Dictionary[ str, __.typx.Any ]( )


class ProcessorCapabilities( __.immut.DataclassObject ):
    ''' Complete capability description for a processor. '''

    processor_name: str
    version: str
    supported_filters: list[ FilterCapability ]
    results_limit_max: __.typx.Optional[ int ] = None
    response_time_typical: __.typx.Optional[ str ] = None  # "fast", etc.
    notes: __.typx.Optional[ str ] = None


class Processor( __.immut.DataclassProtocol ):
    ''' Abstract base class for documentation source detectors. '''

    name: str

    @property
    @__.abc.abstractmethod
    def capabilities( self ) -> ProcessorCapabilities:
        ''' Returns processor capabilities for advertisement. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def detect( self, source: str ) -> 'Detection':
        ''' Detects if can process documentation from source. '''
        raise NotImplementedError



class Detection( __.immut.DataclassProtocol ):
    ''' Abstract base class for documentation detector selections. '''

    processor: Processor
    confidence: float
    timestamp: float = __.dcls.field( default_factory = __.time.time )

    @property
    def capabilities( self ) -> ProcessorCapabilities:
        ''' Returns capabilities for processor. '''
        return self.processor.capabilities

    def __post_init__( self ) -> None:
        ''' Validates confidence is in valid range [0.0, 1.0]. '''
        if not ( 0.0 <= self.confidence <= 1.0 ):
            raise _exceptions.DetectionConfidenceInvalidity( self.confidence )

    @classmethod
    @__.abc.abstractmethod
    async def from_source(
        selfclass, processor: Processor, source: str
    ) -> __.typx.Self:
        ''' Constructs detection from source location. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def extract_documentation_for_objects(
        self, source: str,
        objects: __.cabc.Sequence[ __.cabc.Mapping[ str, __.typx.Any ] ], /, *,
        include_snippets: bool = True,
    ) -> list[ dict[ str, __.typx.Any ] ]:
        ''' Extracts documentation content for specified objects. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def extract_filtered_inventory(
        self, source: str, /, *,
        filters: __.cabc.Mapping[ str, __.typx.Any ],
        details: 'InventoryQueryDetails' = (
            InventoryQueryDetails.Documentation ),
    ) -> list[ dict[ str, __.typx.Any ] ]:
        ''' Extracts and filters inventory objects from source. '''
        raise NotImplementedError


class DetectionToolResponse( __.immut.DataclassObject ):
    ''' Response from detect tool. '''

    source: str
    detections: list[ Detection ]
    detection_best: __.typx.Optional[ Detection ]
    time_detection_ms: int
