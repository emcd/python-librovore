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


DetectionSpecifics: __.typx.TypeAlias = __.typx.Annotated[
    dict[ str, __.typx.Any ],
    __.typx.Doc( ''' Metadata specific to a detection. ''' ),
]


class DisplayStreams( __.enum.Enum ):
    ''' Stream upon which to place output. '''

    Stderr = 'stderr'
    Stdout = 'stdout'


class ConsoleDisplay( __.immut.DataclassObject ):
    silence: __.typx.Annotated[
        bool,
        __.tyro.conf.arg(
            aliases = ( '--quiet', '--silent', ), prefix_name = False ),
    ] = False
    file: __.typx.Annotated[
        __.typx.Optional[ __.Path ],
        __.tyro.conf.arg(
            name = 'console-capture-file', prefix_name = False ),
    ] = None
    stream: __.typx.Annotated[
        DisplayStreams,
        __.tyro.conf.arg( name = 'console-stream', prefix_name = False ),
    ] = DisplayStreams.Stderr

    async def provide_stream( self ) -> __.io.TextIOWrapper:
        ''' Provides output stream for display. '''
        if self.file: return open( self.file, 'w' )
        match self.stream:
            case DisplayStreams.Stdout:
                return __.sys.stdout # pyright: ignore[reportReturnType]
            case DisplayStreams.Stderr:
                return __.sys.stderr # pyright: ignore[reportReturnType]


class CliCommand(
    __.immut.DataclassProtocol, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' CLI command. '''

    @__.abc.abstractmethod
    async def __call__(
        self, auxdata: __.Globals, display: ConsoleDisplay
    ) -> None:
        ''' Executes command with global state. '''
        raise NotImplementedError


class MatchMode( str, __.enum.Enum ):
    ''' Enumeration for different term matching modes. '''

    Exact = 'exact'
    Regex = 'regex'
    Fuzzy = 'fuzzy'


class Processor( __.immut.DataclassProtocol ):
    ''' Abstract base class for documentation source detectors. '''

    name: str

    @__.abc.abstractmethod
    async def detect( self, source: str ) -> 'Detection':
        ''' Detects if can process documentation from source. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def extract_inventory( self, source: str, /, *, # noqa: PLR0913
        domain: __.Absential[ str ] = __.absent,
        role: __.Absential[ str ] = __.absent,
        term: __.Absential[ str ] = __.absent,
        priority: __.Absential[ str ] = __.absent,
        match_mode: MatchMode = MatchMode.Exact,
        fuzzy_threshold: int = 50,
    ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        ''' Extracts inventory from source with optional filtering. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def summarize_inventory( self, source: str, /, *, # noqa: PLR0913
        domain: __.Absential[ str ] = __.absent,
        role: __.Absential[ str ] = __.absent,
        term: __.Absential[ str ] = __.absent,
        priority: __.Absential[ str ] = __.absent,
        match_mode: MatchMode = MatchMode.Exact,
        fuzzy_threshold: int = 50,
    ) -> str:
        ''' Provides human-readable summary of inventory. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def extract_documentation( self, source: str, object_name: str, /, *,
        include_sections: __.Absential[ list[ str ] ] = __.absent,
    ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        ''' Extracts documentation for a specific object from source. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def query_documentation( self, source: str, query: str, /, *, # noqa: PLR0913
        domain: __.Absential[ str ] = __.absent,
        role: __.Absential[ str ] = __.absent,
        priority: __.Absential[ str ] = __.absent,
        match_mode: MatchMode = MatchMode.Fuzzy,
        fuzzy_threshold: int = 50,
        max_results: int = 10,
        include_snippets: bool = True,
    ) -> list[ __.cabc.Mapping[ str, __.typx.Any ] ]:
        ''' Queries documentation content with relevance ranking. '''
        raise NotImplementedError


class Detection( __.immut.DataclassProtocol ):
    ''' Abstract base class for documentation detector selections. '''

    processor: Processor
    confidence: float

    @classmethod
    @__.abc.abstractmethod
    async def from_source(
        selfclass, processor: Processor, source: str
    ) -> __.typx.Self:
        ''' Constructs detection from source location. '''
        raise NotImplementedError

    @property
    @__.abc.abstractmethod
    def specifics( self ) -> DetectionSpecifics:
        ''' Returns metadata associated with detection as dictionary. '''
        raise NotImplementedError
