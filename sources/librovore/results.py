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


''' Results structures.

    Search results, inventory objects, content documents, etc....
'''


from . import __


_CONTENT_PREVIEW_LIMIT = 100


class InventoryObject( __.immut.DataclassObject ):
    ''' Universal inventory object with complete source attribution.

        Represents a single documentation object from any inventory source
        with standardized fields and format-specific metadata container.
    '''

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
    display_name: __.typx.Annotated[
        __.typx.Optional[ str ],
        __.ddoc.Doc( "Human-readable name if different from name." ),
    ] = None
    specifics: __.typx.Annotated[
        __.immut.Dictionary[ str, __.typx.Any ],
        __.ddoc.Doc(
            "Format-specific metadata (domain, role, priority, etc.)." ),
    ] = __.dcls.field( default_factory = lambda: __.immut.Dictionary( ) )


    @property
    def effective_display_name( self ) -> str:
        ''' Effective display name. Might be same as name. '''
        if self.display_name is not None:
            return self.display_name
        return self.name

    @__.abc.abstractmethod
    def render_specifics_json(
        self
    ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders specifics for JSON output. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def render_specifics_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( '''
                Controls whether implementation-specific details (internal
                field names, version numbers, priority scores) are included.
                When False, only user-facing information is shown.
            ''' ),
        ] = True,
    ) -> tuple[ str, ... ]:
        ''' Renders specifics as Markdown lines for CLI display. '''
        raise NotImplementedError

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders complete object as JSON-compatible dictionary. '''
        base = __.immut.Dictionary[
            str, __.typx.Any
        ](
            name = self.name,
            uri = self.uri,
            inventory_type = self.inventory_type,
            location_url = self.location_url,
            display_name = self.display_name,
            effective_display_name = self.effective_display_name,
        )
        formatted_specifics = self.render_specifics_json( )
        result_dict = dict( base )
        result_dict.update( dict( formatted_specifics ) )
        return __.immut.Dictionary[ str, __.typx.Any ]( result_dict )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = True,
    ) -> tuple[ str, ... ]:
        ''' Renders complete object as Markdown lines for display. '''
        lines = [ f"### `{self.effective_display_name}`" ]
        if reveal_internals:
            lines.append( f"**URI:** {self.uri}" )
            lines.append( f"**Type:** {self.inventory_type}" )
            lines.append( f"**Location:** {self.location_url}" )
        specifics_lines = self.render_specifics_markdown(
            reveal_internals = reveal_internals )
        lines.extend( specifics_lines )
        return tuple( lines )


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
    extraction_metadata: __.typx.Annotated[
        __.immut.Dictionary[ str, __.typx.Any ],
        __.ddoc.Doc( "Metadata from structure processor extraction." ),
    ] = __.dcls.field( default_factory = lambda: __.immut.Dictionary( ) )

    @property
    def has_meaningful_content( self ) -> bool:
        ''' Returns True if document contains useful extracted content. '''
        return bool(
            self.signature or self.description or self.content_snippet )

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders complete document as JSON-compatible dictionary. '''
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            inventory_object = dict( self.inventory_object.render_as_json( ) ),
            signature = self.signature,
            description = self.description,
            content_snippet = self.content_snippet,
            documentation_url = self.documentation_url,
            extraction_metadata = dict( self.extraction_metadata ),
            has_meaningful_content = self.has_meaningful_content,
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = True,
    ) -> tuple[ str, ... ]:
        ''' Renders complete document as Markdown lines for display. '''
        lines = [ f"### `{self.inventory_object.effective_display_name}`" ]
        if self.signature:
            lines.append( f"**Signature:** `{self.signature}`" )
        if self.description:
            lines.append( f"**Description:** {self.description}" )
        if self.content_snippet:
            lines.append( f"**Content:** {self.content_snippet}" )
        if self.documentation_url:
            lines.append( f"**URL:** {self.documentation_url}" )
        if reveal_internals:
            inventory_lines = self.inventory_object.render_specifics_markdown(
                reveal_internals = True )
            lines.extend( inventory_lines )
        return tuple( lines )


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

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders error info as JSON-compatible dictionary. '''
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            type = self.type,
            title = self.title,
            message = self.message,
            suggestion = self.suggestion,
        )


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

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders error response as JSON-compatible dictionary. '''
        return __.immut.Dictionary(
            location = self.location,
            query = self.query,
            error = __.immut.Dictionary[
                str, __.typx.Any
            ](
                type = self.error.type,
                title = self.error.title,
                message = self.error.message,
                suggestion = self.error.suggestion,
            ),
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = True,
    ) -> tuple[ str, ... ]:
        ''' Renders error response as Markdown lines for display. '''
        lines = [ f"## Error: {self.error.title}" ]
        lines.append( f"**Message:** {self.error.message}" )
        if self.error.suggestion:
            lines.append( f"**Suggestion:** {self.error.suggestion}" )
        if reveal_internals:
            lines.append( f"**Location:** {self.location}" )
            lines.append( f"**Query:** {self.query}" )
            lines.append( f"**Error Type:** {self.error.type}" )
        return tuple( lines )


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

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders location info as JSON-compatible dictionary. '''
        return __.immut.Dictionary(
            inventory_type = self.inventory_type,
            location_url = self.location_url,
            processor_name = self.processor_name,
            confidence = self.confidence,
            object_count = self.object_count,
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

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders search metadata as JSON-compatible dictionary. '''
        return __.immut.Dictionary(
            results_count = self.results_count,
            results_max = self.results_max,
            matches_total = self.matches_total,
            search_time_ms = self.search_time_ms,
            results_truncated = self.results_truncated,
        )


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
        ''' Produces search result from inventory object with scoring. '''
        return cls(
            inventory_object = inventory_object,
            score = score,
            match_reasons = tuple( match_reasons ) )

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders search result as JSON-compatible dictionary. '''
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            inventory_object = dict( self.inventory_object.render_as_json( ) ),
            score = self.score,
            match_reasons = list( self.match_reasons ),
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = True,
    ) -> tuple[ str, ... ]:
        ''' Renders search result as Markdown lines for display. '''
        title = "### `{name}` (Score: {score:.2f})".format(
            name = self.inventory_object.effective_display_name,
            score = self.score )
        lines = [ title ]
        if reveal_internals and self.match_reasons:
            reasons = ', '.join( self.match_reasons )
            lines.append( "**Match reasons:** {reasons}".format(
                reasons = reasons ) )
        inventory_lines = self.inventory_object.render_as_markdown(
            reveal_internals = reveal_internals )
        lines.extend( inventory_lines[ 1: ] )  # Skip duplicate title line
        return tuple( lines )


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

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders content query result as JSON-compatible dictionary. '''
        documents_json = [
            dict( doc.render_as_json( ) ) for doc in self.documents ]
        locations_json = [
            dict( loc.render_as_json( ) ) for loc in self.inventory_locations ]
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            location = self.location,
            query = self.query,
            documents = documents_json,
            search_metadata = dict( self.search_metadata.render_as_json( ) ),
            inventory_locations = locations_json,
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = True,
        lines_max: __.typx.Annotated[
            __.typx.Optional[ int ],
            __.ddoc.Doc( "Maximum lines to display per content result." ),
        ] = None,
    ) -> tuple[ str, ... ]:
        ''' Renders content query result as Markdown lines for display. '''
        title = "# Content Query Results"
        if lines_max is not None:
            title += " (truncated)"
        lines = [ title ]
        lines.append( "**Query:** {query}".format( query = self.query ) )
        if reveal_internals:
            lines.append( "**Location:** {location}".format(
                location = self.location ) )
        lines.append( "**Results:** {count} of {max}".format(
            count = self.search_metadata.results_count,
            max = self.search_metadata.results_max ) )
        if self.documents:
            lines.append( "" )
            lines.append( "## Documents" )
            for index, doc in enumerate( self.documents, 1 ):
                separator = "\n📄 ── Document {} ──────────────────── 📄\n"
                lines.append( separator.format( index ) )
                lines.append( "**URL:** {url}".format(
                    url = doc.documentation_url ) )
                if doc.signature:
                    lines.append( "**Signature:** {signature}".format(
                        signature = doc.signature ) )
                if doc.description:
                    lines.append( "**Description:** {description}".format(
                        description = doc.description ) )
                if doc.content_snippet:
                    content = doc.content_snippet
                    if lines_max is not None:
                        content_lines = content.split( '\n' )
                        if len( content_lines ) > lines_max:
                            content_lines = content_lines[ :lines_max ]
                            content_lines.append(
                                "... (truncated at {lines_max} lines)".format(
                                    lines_max = lines_max ) )
                        content = '\n'.join( content_lines )
                    lines.append( "**Content:** {content}".format(
                        content = content ) )
        return tuple( lines )


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

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders inventory query result as JSON-compatible dictionary. '''
        objects_json = [
            dict( obj.render_as_json( ) ) for obj in self.objects ]
        locations_json = [
            dict( loc.render_as_json( ) ) for loc in self.inventory_locations ]
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            location = self.location,
            query = self.query,
            objects = objects_json,
            search_metadata = dict( self.search_metadata.render_as_json( ) ),
            inventory_locations = locations_json,
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = True,
    ) -> tuple[ str, ... ]:
        ''' Renders inventory query result as Markdown lines for display. '''
        lines = [ "# Inventory Query Results" ]
        lines.append( "**Query:** {query}".format( query = self.query ) )
        if reveal_internals:
            lines.append( "**Location:** {location}".format(
                location = self.location ) )
        lines.append( "**Results:** {count} of {max}".format(
            count = self.search_metadata.results_count,
            max = self.search_metadata.results_max ) )
        if self.objects:
            lines.append( "" )
            lines.append( "## Objects" )
            for index, obj in enumerate( self.objects, 1 ):
                separator = "\n📦 ── Object {} ─────────────────────── 📦\n"
                lines.append( separator.format( index ) )
                obj_lines = obj.render_as_markdown(
                    reveal_internals = reveal_internals )
                lines.extend( obj_lines )
        return tuple( lines )


class Detection( __.immut.DataclassObject ):
    ''' Processor detection information with confidence scoring. '''

    processor_name: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Name of the processor that can handle this location." ),
    ]
    confidence: __.typx.Annotated[
        float,
        __.ddoc.Doc( "Detection confidence score (0.0-1.0)." ),
    ]
    processor_type: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Type of processor (inventory, structure)." ),
    ]
    detection_metadata: __.typx.Annotated[
        __.immut.Dictionary[ str, __.typx.Any ],
        __.ddoc.Doc( "Processor-specific detection metadata." ),
    ] = __.dcls.field( default_factory = lambda: __.immut.Dictionary( ) )

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders detection as JSON-compatible dictionary. '''
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            processor_name = self.processor_name,
            confidence = self.confidence,
            processor_type = self.processor_type,
            detection_metadata = dict( self.detection_metadata ),
        )


class DetectionsResult( __.immut.DataclassObject ):
    ''' Detection results with processor selection and timing metadata. '''

    source: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Primary location URL for detection operation." ),
    ]
    detections: __.typx.Annotated[
        tuple[ Detection, ... ],
        __.ddoc.Doc( "All processor detections found for location." ),
    ]
    detection_optimal: __.typx.Annotated[
        __.typx.Optional[ Detection ],
        __.ddoc.Doc( "Best detection result based on confidence scoring." ),
    ]
    time_detection_ms: __.typx.Annotated[
        int,
        __.ddoc.Doc( "Detection operation time in milliseconds." ),
    ]


    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders detection results as JSON-compatible dictionary. '''
        detections_json = [
            dict( detection.render_as_json( ) )
            for detection in self.detections ]
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            source = self.source,
            detections = detections_json,
            detection_optimal = (
                dict( self.detection_optimal.render_as_json( ) )
                if self.detection_optimal else None ),
            time_detection_ms = self.time_detection_ms,
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = True,
    ) -> tuple[ str, ... ]:
        ''' Renders detection results as Markdown lines for display. '''
        lines = [ "# Detection Results" ]
        if reveal_internals:
            lines.append( "**Source:** {source}".format(
                source = self.source ) )
            lines.append( "**Detection time:** {time}ms".format(
                time = self.time_detection_ms ) )
        if self.detection_optimal:
            lines.append( "**Optimal processor:** {name} ({type})".format(
                name = self.detection_optimal.processor_name,
                type = self.detection_optimal.processor_type ) )
            lines.append( "**Confidence:** {conf:.2f}".format(
                conf = self.detection_optimal.confidence ) )
        else:
            lines.append( "**No optimal processor found**" )
        if reveal_internals and self.detections:
            lines.append( "" )
            lines.append( "## All Detections" )
            detection_lines = [
                "- **{name}** ({type}): {conf:.2f}".format(
                    name = detection.processor_name,
                    type = detection.processor_type,
                    conf = detection.confidence )
                for detection in self.detections ]
            lines.extend( detection_lines )
        return tuple( lines )


def serialize_for_json( objct: __.typx.Any ) -> __.typx.Any:
    ''' Legacy serialization for non-structured objects (dicts). '''
    if __.dcls.is_dataclass( objct ):
        return _serialize_dataclass_for_json( objct )
    if isinstance( objct, ( list, tuple, set, frozenset ) ):
        return _serialize_sequence_for_json( objct )
    if isinstance( objct, ( dict, __.immut.Dictionary ) ):
        return _serialize_mapping_for_json( objct )
    return objct


def validate_content_document( doc: ContentDocument ) -> ContentDocument:
    ''' Validates content document has valid inventory object and content. '''
    validate_inventory_object( doc.inventory_object )
    if not doc.has_meaningful_content:
        # TODO: Properly raise error.
        pass
    return doc


def validate_inventory_object( objct: InventoryObject ) -> InventoryObject:
    ''' Validates inventory object has required fields and valid values. '''
    if not objct.name: raise ValueError
    if not objct.uri: raise ValueError
    if not objct.inventory_type: raise ValueError
    if not objct.location_url: raise ValueError
    return objct


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


def _serialize_dataclass_for_json(
    obj: __.typx.Any,
) -> dict[ str, __.typx.Any ]:
    ''' Serializes dataclass objects to JSON-compatible dictionaries. '''
    result: dict[ str, __.typx.Any ] = { }
    for field in __.dcls.fields( obj ):
        if field.name.startswith( '_' ):
            continue
        value = getattr( obj, field.name )
        result[ field.name ] = serialize_for_json( value )
    return result


def _serialize_mapping_for_json(
    obj: __.typx.Any
) -> dict[ __.typx.Any, __.typx.Any ]:
    ''' Serializes mapping-like objects to JSON-compatible dictionaries. '''
    return {
        key: serialize_for_json( value )
        for key, value in obj.items( )
    }


def _serialize_sequence_for_json( obj: __.typx.Any ) -> list[ __.typx.Any ]:
    ''' Serializes sequence-like objects to JSON-compatible lists. '''
    return [ serialize_for_json( item ) for item in obj ]


ContentDocuments: __.typx.TypeAlias = __.cabc.Sequence[ ContentDocument ]
InventoryObjects: __.typx.TypeAlias = __.cabc.Sequence[ InventoryObject ]
SearchResults: __.typx.TypeAlias = __.cabc.Sequence[ SearchResult ]

ContentResult: __.typx.TypeAlias = ContentQueryResult | ErrorResponse
InventoryResult: __.typx.TypeAlias = InventoryQueryResult | ErrorResponse
DetectionsResultUnion: __.typx.TypeAlias = DetectionsResult | ErrorResponse
