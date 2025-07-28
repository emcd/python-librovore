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


class MatchMode( str, __.enum.Enum ):
    ''' Enumeration for different term matching modes. '''

    Exact = 'exact'
    Regex = 'regex'
    Fuzzy = 'fuzzy'


class Filters( __.immut.DataclassObject ):
    ''' Common filters for inventory and documentation search. '''

    domain: str = ""
    role: str = ""
    priority: str = ""
    match_mode: MatchMode = MatchMode.Fuzzy
    fuzzy_threshold: int = 50


class Processor( __.immut.DataclassProtocol ):
    ''' Abstract base class for documentation source detectors. '''

    name: str

    @__.abc.abstractmethod
    async def detect( self, source: str ) -> 'Detection':
        ''' Detects if can process documentation from source. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def extract_inventory( self, source: str, /, *,
        term: __.Absential[ str ] = __.absent,
        filters: Filters,
    ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        ''' Extracts inventory from source with optional filtering. '''
        raise NotImplementedError


    @__.abc.abstractmethod
    async def extract_documentation( self, source: str, object_name: str, /, *,
        include_sections: __.Absential[ list[ str ] ] = __.absent,
    ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        ''' Extracts documentation for a specific object from source. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def query_documentation( self, source: str, query: str, /, *,
        filters: Filters,
        include_snippets: bool = True,
        results_max: int = 10,
    ) -> list[ __.cabc.Mapping[ str, __.typx.Any ] ]:
        ''' Queries documentation content with relevance ranking. '''
        raise NotImplementedError


class Detection( __.immut.DataclassProtocol ):
    ''' Abstract base class for documentation detector selections. '''

    processor: Processor
    confidence: float
    timestamp: float = __.dcls.field( default_factory = __.time.time )

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
