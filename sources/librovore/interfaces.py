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


class DisplayFormat( __.enum.Enum ):
    ''' Enumeration for CLI display formats. '''

    JSON = 'json'
    Markdown = 'markdown'


class FilterCapability( __.immut.DataclassObject ):
    ''' Describes a filter supported by a processor. '''

    name: str
    description: str
    type: str  # "string", "enum", "boolean"
    values: __.typx.Optional[ list[ str ] ] = None  # For enums
    required: bool = False


class ProcessorGenera( __.enum.Enum ):
    ''' Processor types/genera. '''

    Inventory = 'inventory'
    Structure = 'structure'



class MatchMode( str, __.enum.Enum ):
    ''' Different term matching modes. '''

    Exact = 'exact'
    Similar = 'similar'
    Pattern = 'pattern'


class ContentExtractionFeatures( str, __.enum.Enum ):
    ''' Content extraction capability features. '''

    Signatures = 'signatures'           # Function/class signatures
    Descriptions = 'descriptions'       # Descriptive content and documentation
    Arguments = 'arguments'             # Individual parameter documentation
    Returns = 'returns'                 # Return value documentation
    Attributes = 'attributes'           # Class and module attribute docs
    CodeExamples = 'code-examples'      # Code blocks with language information
    CrossReferences = 'cross-references' # Links and references to other docs
    Navigation = 'navigation'           # Navigation context extraction


class SearchBehaviors( __.immut.DataclassObject ):
    ''' Search behavior configuration for the search engine. '''

    match_mode: MatchMode = MatchMode.Similar
    similarity_score_min: int = 50
    contains_term: __.typx.Annotated[
        bool,
        __.ddoc.Doc(
            "Enable substring matching in Exact and Similar modes. "
            "When enabled, allows terms to match as substrings." ),
    ] = True
    case_sensitive: __.typx.Annotated[
        bool,
        __.ddoc.Doc(
            "Enable case-sensitive matching. When False, "
            "performs case-insensitive matching (default)." ),
    ] = False


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

    def render_as_json( self ) -> dict[ str, __.typx.Any ]:
        ''' Renders capabilities as JSON-compatible dictionary. '''
        return {
            'processor_name': self.processor_name,
            'version': self.version,
            'supported_filters': [
                {
                    'name': filter_cap.name,
                    'type': filter_cap.type,
                    'required': filter_cap.required,
                    'description': filter_cap.description,
                }
                for filter_cap in self.supported_filters
            ],
            'results_limit_max': self.results_limit_max,
            'response_time_typical': self.response_time_typical,
            'notes': self.notes,
        }

    def render_as_markdown( self ) -> tuple[ str, ... ]:
        ''' Renders capabilities as Markdown lines for display. '''
        lines = [ f"**Version:** {self.version}" ]
        if self.results_limit_max:
            lines.append( f"**Max results:** {self.results_limit_max}" )
        if self.response_time_typical:
            lines.append( f"**Response time:** {self.response_time_typical}" )
        if self.notes:
            lines.append( f"**Notes:** {self.notes}" )
        if self.supported_filters:
            lines.append( "" )
            lines.append( "**Supported filters:**" )
            for filter_cap in self.supported_filters:
                filter_line = f"- `{filter_cap.name}` ({filter_cap.type})"
                if filter_cap.required:
                    filter_line += " *required*"
                if filter_cap.description:
                    filter_line += f": {filter_cap.description}"
                lines.append( filter_line )
        return tuple( lines )


class StructureProcessorCapabilities( __.immut.DataclassObject ):
    ''' Capability advertisement for structure processors. '''

    supported_inventory_types: frozenset[ str ]
    content_extraction_features: frozenset[ ContentExtractionFeatures ]
    confidence_by_inventory_type: __.immut.Dictionary[ str, float ]

    def get_confidence_for_type( self, inventory_type: str ) -> float:
        ''' Gets extraction confidence for inventory type.

            The confidence score (0.0-1.0) indicates how well this processor
            can extract content from the inventory type. Used for processor
            selection when multiple processors support the same type.
        '''
        return self.confidence_by_inventory_type.get( inventory_type, 0.0 )

    def supports_inventory_type( self, inventory_type: str ) -> bool:
        ''' Checks if processor supports specified inventory type. '''
        return inventory_type in self.supported_inventory_types
