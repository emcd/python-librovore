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


''' Structured dataclass objects representing search results,
    inventory objects, and content documents.
'''


from . import __


class InventoryObject( __.immut.DataclassObject ):
    ''' Universal inventory object with complete source attribution.
    
        Represents a single documentation object from any inventory source
        with standardized fields and format-specific metadata container.
    '''
    
    # Universal identification fields
    name: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Primary object identifier from inventory source." ),
    ]
    uri: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Relative URI to object documentation content." ),
    ]
    inventory_type: __.typx.Annotated[
        str,
        __.ddoc.Doc(
            "Inventory format identifier (e.g., sphinx_objects_inv)." ),
    ]
    location_url: __.typx.Annotated[
        str, __.ddoc.Doc(
            "Complete URL to inventory location for attribution." )
    ]
    
    # Optional display enhancement
    display_name: __.typx.Annotated[
        __.typx.Optional[ str ],
        __.ddoc.Doc( "Human-readable name if different from name." ),
    ] = None
    
    # Format-specific metadata container
    specifics: __.typx.Annotated[
        __.immut.Dictionary[ str, __.typx.Any ],
        __.ddoc.Doc(
            "Format-specific metadata (domain, role, priority, etc.)." ),
    ] = __.dcls.field( default_factory = lambda: __.immut.Dictionary( ) )
    
    
    @property
    def effective_display_name( self ) -> str:
        ''' Returns display_name if available, otherwise falls back to
            name.
        '''
        if self.display_name is not None:
            return self.display_name
        return self.name
    
    def to_json_dict( self ) -> dict[ str, __.typx.Any ]:
        ''' Returns JSON-compatible dictionary representation. '''
        result: dict[ str, __.typx.Any ] = {
            'name': self.name,
            'uri': self.uri,
            'inventory_type': self.inventory_type,
            'location_url': self.location_url,
            'display_name': self.display_name,
            'effective_display_name': self.effective_display_name,
        }
        specifics_dict = dict( self.specifics )
        result.update( specifics_dict )
        return result


class SearchResult( __.immut.DataclassObject ):
    ''' Search result with inventory object and match metadata. '''
    
    inventory_object: __.typx.Annotated[
        InventoryObject,
        __.ddoc.Doc( "Matched inventory object with metadata." ),
    ]
    score: __.typx.Annotated[
        float,
        __.ddoc.Doc( "Search relevance score (0.0-1.0)." ),
    ]
    match_reasons: __.typx.Annotated[
        tuple[ str, ... ],
        __.ddoc.Doc( "Detailed reasons for search match." ),
    ]
    
    @classmethod
    def from_inventory_object(
        cls,
        inventory_object: InventoryObject, *,
        score: float,
        match_reasons: __.cabc.Sequence[ str ],
    ) -> __.typx.Self:
        ''' Creates search result from inventory object with scoring. '''
        return cls(
            inventory_object = inventory_object,
            score = score,
            match_reasons = tuple( match_reasons ) )


class ContentDocument( __.immut.DataclassObject ):
    ''' Documentation content with extracted metadata and snippets. '''
    
    inventory_object: __.typx.Annotated[
        InventoryObject,
        __.ddoc.Doc( "Location inventory object for this content." ),
    ]
    signature: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Extracted function/class signature." ),
    ] = ''
    description: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Extracted object description or summary." ),
    ] = ''
    content_snippet: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Relevant content excerpt for search context." ),
    ] = ''
    documentation_url: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Complete URL to full documentation page." ),
    ] = ''
    
    # Structure processor metadata
    extraction_metadata: __.typx.Annotated[
        __.immut.Dictionary[ str, __.typx.Any ],
        __.ddoc.Doc( "Metadata from structure processor extraction." ),
    ] = __.dcls.field( default_factory = lambda: __.immut.Dictionary( ) )
    
    @property
    def has_meaningful_content( self ) -> bool:
        ''' Returns True if document contains useful extracted content.
        '''
        return bool(
            self.signature or self.description or self.content_snippet
        )


class SearchMetadata( __.immut.DataclassObject ):
    ''' Search operation metadata and performance statistics. '''
    
    results_count: __.typx.Annotated[
        int,
        __.ddoc.Doc( "Number of results returned to user." ),
    ]
    results_max: __.typx.Annotated[
        int,
        __.ddoc.Doc( "Maximum results requested by user." ),
    ]
    matches_total: __.typx.Annotated[
        __.typx.Optional[ int ],
        __.ddoc.Doc( "Total matching objects before limit applied." ),
    ] = None
    search_time_ms: __.typx.Annotated[
        __.typx.Optional[ int ],
        __.ddoc.Doc( "Search execution time in milliseconds." ),
    ] = None
    
    @property
    def results_truncated( self ) -> bool:
        ''' Returns True if results were limited by results_max. '''
        if self.matches_total is None:
            return False
        return self.results_count < self.matches_total


class InventoryLocationInfo( __.immut.DataclassObject ):
    ''' Information about detected inventory location and processor. '''
    
    inventory_type: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Inventory format type identifier." ),
    ]
    location_url: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Complete URL to inventory location." ),
    ]
    processor_name: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Name of processor handling this location." ),
    ]
    confidence: __.typx.Annotated[
        float,
        __.ddoc.Doc( "Detection confidence score (0.0-1.0)." ),
    ]
    object_count: __.typx.Annotated[
        int,
        __.ddoc.Doc( "Total objects available in this inventory." ),
    ]


class InventoryQueryResult( __.immut.DataclassObject ):
    ''' Complete result structure for inventory queries. '''
    
    location: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Primary location URL for this query." ),
    ]
    query: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Search term or query string used." ),
    ]
    objects: __.typx.Annotated[
        tuple[ InventoryObject, ... ],
        __.ddoc.Doc( "Inventory objects matching search criteria." ),
    ]
    search_metadata: __.typx.Annotated[
        SearchMetadata,
        __.ddoc.Doc( "Search execution and result metadata." ),
    ]
    inventory_locations: __.typx.Annotated[
        tuple[ InventoryLocationInfo, ... ],
        __.ddoc.Doc( "Information about inventory locations used." ),
    ]


class ContentQueryResult( __.immut.DataclassObject ):
    ''' Complete result structure for content queries. '''
    
    location: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Primary location URL for this query." ),
    ]
    query: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Search term or query string used." ),
    ]
    documents: __.typx.Annotated[
        tuple[ ContentDocument, ... ],
        __.ddoc.Doc( "Documentation content for matching objects." ) ]
    search_metadata: __.typx.Annotated[
        SearchMetadata,
        __.ddoc.Doc( "Search execution and result metadata." ),
    ]
    inventory_locations: __.typx.Annotated[
        tuple[ InventoryLocationInfo, ... ],
        __.ddoc.Doc( "Information about inventory locations used." ),
    ]


class ErrorInfo( __.immut.DataclassObject ):
    ''' Structured error information for processor failures. '''
    
    type: __.typx.Annotated[
        str,
        __.ddoc.Doc(
            "Error type identifier (e.g., 'processor_unavailable')." ),
    ]
    title: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Human-readable error title." ),
    ]
    message: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Detailed error description." ),
    ]
    suggestion: __.typx.Annotated[
        __.typx.Optional[ str ],
        __.ddoc.Doc( "Suggested remediation steps." ),
    ] = None


class ErrorResponse( __.immut.DataclassObject ):
    ''' Error response wrapper maintaining query context. '''
    
    location: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Primary location URL for failed query." ),
    ]
    query: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Search term or query string that failed." ),
    ]
    error: __.typx.Annotated[
        ErrorInfo,
        __.ddoc.Doc( "Detailed error information." ),
    ]


def validate_inventory_object( obj: InventoryObject ) -> InventoryObject:
    ''' Validates inventory object has required fields and valid values. '''
    if not obj.name: raise ValueError
    if not obj.uri: raise ValueError
    if not obj.inventory_type: raise ValueError
    if not obj.location_url: raise ValueError
    return obj


def validate_search_result( result: SearchResult ) -> SearchResult:
    ''' Validates search result consistency and score alignment. '''
    if not ( 0.0 <= result.score <= 1.0 ):
        message = (
            f"SearchResult score must be between 0.0 and 1.0, "
            f"got {result.score}."
        )
        raise ValueError( message )
    validate_inventory_object( result.inventory_object )
    return result


def validate_content_document( doc: ContentDocument ) -> ContentDocument:
    ''' Validates content document has valid inventory object and content. '''
    validate_inventory_object( doc.inventory_object )
    if not doc.has_meaningful_content:
        # TODO: Consider logging warning for empty content documents
        # or implementing configurable validation strictness levels
        pass
    return doc


def serialize_for_json( obj: __.typx.Any ) -> __.typx.Any:
    ''' Serialization supporting structured result objects. '''
    if isinstance( obj, InventoryObject ):
        return obj.to_json_dict( )
    if (
        isinstance( obj, ( InventoryQueryResult, ContentQueryResult ) )
        or __.dcls.is_dataclass( obj )
    ):
        return _serialize_dataclass_for_json( obj )
    if isinstance( obj, ( list, tuple, set, frozenset ) ):
        return _serialize_sequence_for_json( obj )
    if isinstance( obj, ( dict, __.immut.Dictionary ) ):
        return _serialize_mapping_for_json( obj )
    return obj


def _serialize_sequence_for_json( obj: __.typx.Any ) -> list[ __.typx.Any ]:
    ''' Serializes sequence-like objects to JSON-compatible lists. '''
    return [ serialize_for_json( item ) for item in obj ]


def _serialize_mapping_for_json(
    obj: __.typx.Any
) -> dict[ __.typx.Any, __.typx.Any ]:
    ''' Serializes mapping-like objects to JSON-compatible dictionaries. '''
    return {
        key: serialize_for_json( value )
        for key, value in obj.items( )
    }


def _serialize_dataclass_for_json(
    obj: __.typx.Any,
) -> dict[ str, __.typx.Any ]:
    ''' Serializes dataclass objects to JSON-compatible dictionaries. '''
    if hasattr( obj, 'to_json_dict' ):
        return obj.to_json_dict( )
    result: dict[ str, __.typx.Any ] = { }
    for field in __.dcls.fields( obj ):
        if field.name.startswith( '_' ):
            continue
        value = getattr( obj, field.name )
        result[ field.name ] = serialize_for_json( value )
    return result


InventoryObjects: __.typx.TypeAlias = __.cabc.Sequence[ InventoryObject ]
SearchResults: __.typx.TypeAlias = __.cabc.Sequence[ SearchResult ]
ContentDocuments: __.typx.TypeAlias = __.cabc.Sequence[ ContentDocument ]

# Union types for error propagation
InventoryResult: __.typx.TypeAlias = InventoryQueryResult | ErrorResponse
ContentResult: __.typx.TypeAlias = ContentQueryResult | ErrorResponse