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
from . import exceptions as _exceptions


_CONTENT_PREVIEW_LIMIT = 100


class ResultBase( __.immut.DataclassProtocol, __.typx.Protocol ):
    ''' Base protocol for all result objects with rendering methods. '''

    @__.abc.abstractmethod
    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders result as JSON-compatible dictionary. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def render_as_markdown(
        self, /, *,
        reveal_internals: bool = False,
    ) -> tuple[ str, ... ]:
        ''' Renders result as Markdown lines for display. '''
        raise NotImplementedError


class InventoryObject( ResultBase ):
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
        self, /, *,
        reveal_internals: bool = False,
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
        ] = False,
    ) -> tuple[ str, ... ]:
        ''' Renders specifics as Markdown lines for CLI display. '''
        raise NotImplementedError

    def render_as_json(
        self, /, *,
        reveal_internals: bool = False,
    ) -> __.immut.Dictionary[ str, __.typx.Any ]:
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
        formatted_specifics = self.render_specifics_json(
            reveal_internals = reveal_internals )
        result_dict = dict( base )
        result_dict.update( dict( formatted_specifics ) )
        return __.immut.Dictionary[ str, __.typx.Any ]( result_dict )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = False,
    ) -> tuple[ str, ... ]:
        ''' Renders complete object as Markdown lines for display. '''
        lines = [ f"### `{self.effective_display_name}`" ]
        lines.append( f"- **URI:** {self.uri}" )
        lines.append( f"- **Type:** {self.inventory_type}" )
        lines.append( f"- **Location:** {self.location_url}" )
        specifics_lines = self.render_specifics_markdown(
            reveal_internals = reveal_internals )
        lines.extend( specifics_lines )
        return tuple( lines )


class ContentDocument( ResultBase ):
    ''' Documentation content with extracted metadata and content ID. '''

    inventory_object: __.typx.Annotated[
        InventoryObject,
        __.ddoc.Doc( "Location inventory object for this content." ),
    ]
    content_id: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Deterministic identifier for content retrieval." ),
    ]
    description: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Extracted object description or summary." ),
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
        return bool( self.description )

    def render_as_json( 
        self, /, *,
        lines_max: __.typx.Optional[ int ] = None,
    ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders complete document as JSON-compatible dictionary. '''
        description = self.description
        if lines_max is not None:
            desc_lines = description.split( '\n' )
            if len( desc_lines ) > lines_max:
                desc_lines = desc_lines[ :lines_max ]
                desc_lines.append( "..." )
            description = '\n'.join( desc_lines )
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            inventory_object = dict( self.inventory_object.render_as_json( ) ),
            content_id = self.content_id,
            description = description,
            documentation_url = self.documentation_url,
            extraction_metadata = dict( self.extraction_metadata ),
            has_meaningful_content = self.has_meaningful_content,
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = False,
        lines_max: __.typx.Annotated[
            __.typx.Optional[ int ],
            __.ddoc.Doc( "Maximum lines to display for description." ),
        ] = None,
        include_title: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Whether to include document title header." ),
        ] = True,
    ) -> tuple[ str, ... ]:
        ''' Renders complete document as Markdown lines for display. '''
        lines: list[ str ] = [ ]
        if include_title:
            lines.append( 
                f"### `{self.inventory_object.effective_display_name}`" )
        metadata_lines: list[ str ] = [ ]
        if self.documentation_url:
            metadata_lines.append( f"- **URL:** {self.documentation_url}" )
        metadata_lines.append( f"- **Content ID:** `{self.content_id}`" )
        if metadata_lines:
            lines.extend( metadata_lines )
        inventory_lines = self.inventory_object.render_specifics_markdown(
            reveal_internals = reveal_internals )
        if inventory_lines:
            lines.extend( inventory_lines )
        if self.description:
            lines.append( "" )
            description = self.description
            if lines_max is not None:
                desc_lines = description.split( '\n' )
                if len( desc_lines ) > lines_max:
                    desc_lines = desc_lines[ :lines_max ]
                    desc_lines.append( "..." )
                description = '\n'.join( desc_lines )
            lines.append( description )
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


class SearchResult( ResultBase ):
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
        ] = False,
    ) -> tuple[ str, ... ]:
        ''' Renders search result as Markdown lines for display. '''
        title = "### `{name}` (Score: {score:.2f})".format(
            name = self.inventory_object.effective_display_name,
            score = self.score )
        lines = [ title ]
        if reveal_internals and self.match_reasons:
            reasons = ', '.join( self.match_reasons )
            lines.append( "- **Match reasons:** {reasons}".format(
                reasons = reasons ) )
        inventory_lines = self.inventory_object.render_as_markdown(
            reveal_internals = reveal_internals )
        lines.extend( inventory_lines[ 1: ] )  # Skip duplicate title line
        return tuple( lines )


class ContentQueryResult( ResultBase ):
    ''' Complete result structure for content queries. '''

    location: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Primary location URL for this query." ),
    ]
    term: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Search term used for this query." ),
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

    def render_as_json( 
        self, /, *,
        lines_max: __.typx.Optional[ int ] = None,
    ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders content query result as JSON-compatible dictionary. '''
        documents_json = [
            dict( doc.render_as_json( lines_max = lines_max ) ) 
            for doc in self.documents ]
        locations_json = [
            dict( loc.render_as_json( ) ) for loc in self.inventory_locations ]
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            location = self.location,
            term = self.term,
            documents = documents_json,
            search_metadata = dict( self.search_metadata.render_as_json( ) ),
            inventory_locations = locations_json,
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = False,
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
        lines.append( "- **Term:** {term}".format( term = self.term ) )
        if reveal_internals:
            lines.append( "- **Location:** {location}".format(
                location = self.location ) )
        lines.append( "- **Results:** {count} of {max}".format(
            count = self.search_metadata.results_count,
            max = self.search_metadata.results_max ) )
        if self.documents:
            lines.append( "" )
            lines.append( "## Documents" )
            for index, doc in enumerate( self.documents, 1 ):
                separator = "\n📄 ── Document {} ──────────────────── 📄\n"
                lines.append( separator.format( index ) )
                doc_lines = doc.render_as_markdown( 
                    reveal_internals = reveal_internals,
                    lines_max = lines_max,
                    include_title = False )
                lines.extend( doc_lines )
        return tuple( lines )


class InventoryQueryResult( ResultBase ):
    ''' Complete result structure for inventory queries. '''

    location: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Primary location URL for this query." ),
    ]
    term: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Search term used for this query." ),
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

    def render_as_json(
        self, /, *,
        reveal_internals: bool = False,
    ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders inventory query result as JSON-compatible dictionary. '''
        objects_json = [
            dict( obj.render_as_json( reveal_internals = reveal_internals ) )
            for obj in self.objects ]
        locations_json = [
            dict( loc.render_as_json( ) ) for loc in self.inventory_locations ]
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            location = self.location,
            term = self.term,
            objects = objects_json,
            search_metadata = dict( self.search_metadata.render_as_json( ) ),
            inventory_locations = locations_json,
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = False,
    ) -> tuple[ str, ... ]:
        ''' Renders inventory query result as Markdown lines for display. '''
        lines = [ "# Inventory Query Results" ]
        lines.append( "- **Term:** {term}".format( term = self.term ) )
        if reveal_internals:
            lines.append( "- **Location:** {location}".format(
                location = self.location ) )
        lines.append( "- **Results:** {count} of {max}".format(
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


class DetectionsResult( ResultBase ):
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
        ] = False,
    ) -> tuple[ str, ... ]:
        ''' Renders detection results as Markdown lines for display. '''
        lines = [ "# Detection Results" ]
        if reveal_internals:
            lines.append( "- **Source:** {source}".format(
                source = self.source ) )
            lines.append( "- **Detection time:** {time}ms".format(
                time = self.time_detection_ms ) )
        if self.detection_optimal:
            lines.append( "- **Optimal processor:** {name} ({type})".format(
                name = self.detection_optimal.processor_name,
                type = self.detection_optimal.processor_type ) )
            lines.append( "- **Confidence:** {conf:.2f}".format(
                conf = self.detection_optimal.confidence ) )
        else:
            lines.append( "- **No optimal processor found**" )
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


class ProcessorInfo( ResultBase ):
    ''' Information about a processor and its capabilities. '''

    processor_name: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Name of the processor for identification." ),
    ]
    processor_type: __.typx.Annotated[
        str,
        __.ddoc.Doc( "Type of processor (inventory, structure)." ),
    ]
    capabilities: __.typx.Annotated[
        __.typx.Any,  # Will be _interfaces.ProcessorCapabilities after import
        __.ddoc.Doc( "Complete capability description for processor." ),
    ]

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders processor info as JSON-compatible dictionary. '''
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            processor_name = self.processor_name,
            processor_type = self.processor_type,
            capabilities = self.capabilities.render_as_json( ),
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = False,
    ) -> tuple[ str, ... ]:
        ''' Renders processor info as Markdown lines for display. '''
        lines = [ f"### `{self.processor_name}` ({self.processor_type})" ]
        if reveal_internals:
            capabilities_lines = self.capabilities.render_as_markdown( )
            lines.extend( capabilities_lines )
        return tuple( lines )


class ProcessorsSurveyResult( ResultBase ):
    ''' Survey results listing available processors and capabilities. '''

    genus: __.typx.Annotated[
        __.typx.Any,  # Will be _interfaces.ProcessorGenera after import
        __.ddoc.Doc( 
            "Processor genus that was surveyed (inventory or structure)." ),
    ]
    filter_name: __.typx.Annotated[
        __.typx.Optional[ str ],
        __.ddoc.Doc( "Optional processor name filter applied to survey." ),
    ] = None
    processors: __.typx.Annotated[
        tuple[ ProcessorInfo, ... ],
        __.ddoc.Doc( "Available processors matching survey criteria." ),
    ]
    survey_time_ms: __.typx.Annotated[
        int,
        __.ddoc.Doc( "Survey operation time in milliseconds." ),
    ]

    def render_as_json( self ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders survey results as JSON-compatible dictionary. '''
        processors_json = [
            dict( processor.render_as_json( ) )
            for processor in self.processors ]
        return __.immut.Dictionary[
            str, __.typx.Any
        ](
            genus = (
                self.genus.value if hasattr( self.genus, 'value' ) 
                else str( self.genus ) ),
            filter_name = self.filter_name,
            processors = processors_json,
            survey_time_ms = self.survey_time_ms,
        )

    def render_as_markdown(
        self, /, *,
        reveal_internals: __.typx.Annotated[
            bool,
            __.ddoc.Doc( "Controls whether internal details are shown." ),
        ] = False,
    ) -> tuple[ str, ... ]:
        ''' Renders survey results as Markdown lines for display. '''
        genus_name = (
            self.genus.value if hasattr( self.genus, 'value' ) 
            else str( self.genus ) )
        title = f"# Processor Survey Results ({genus_name})"
        lines = [ title ]
        if reveal_internals:
            lines.append( f"- **Survey time:** {self.survey_time_ms}ms" )
            if self.filter_name:
                lines.append( f"- **Filter:** {self.filter_name}" )
        lines.append( f"- **Processors found:** {len( self.processors )}" )
        if self.processors:
            lines.append( "" )
            for i, processor in enumerate( self.processors, 1 ):
                lines.append( f"📦 ── Processor {i} ──────────" )
                processor_lines = processor.render_as_markdown( 
                    reveal_internals = reveal_internals )
                lines.extend( processor_lines )
                if i < len( self.processors ):
                    lines.append( "" )
        return tuple( lines )


def parse_content_id( content_id: str ) -> tuple[ str, str ]:
    ''' Parses content identifier back to location and name components.
    
        Returns tuple of (location, name) extracted from content_id.
        Raises ContentIdInvalidity if content_id is malformed or cannot be 
        decoded.
    '''
    try:
        identifier_source = __.base64.b64decode( 
            content_id.encode( 'ascii' ) ).decode( 'utf-8' )
    except Exception as exc:
        raise _exceptions.ContentIdInvalidity( 
            content_id, "Base64 decoding failed" ) from exc
    if ':' not in identifier_source:
        raise _exceptions.ContentIdInvalidity( 
            content_id, "Missing location:object separator" )
    location, name = identifier_source.rsplit( ':', 1 )
    return location, name


def produce_content_id( location: str, name: str ) -> str:
    ''' Produces deterministic content identifier for browse-then-extract.
    
        Uses base64 encoding of location + ":" + name to create stable,
        debuggable identifiers that maintain stateless operation.
    '''
    identifier_source = f"{location}:{name}"
    return __.base64.b64encode( 
        identifier_source.encode( 'utf-8' ) ).decode( 'ascii' )







ContentDocuments: __.typx.TypeAlias = __.cabc.Sequence[ ContentDocument ]
InventoryObjects: __.typx.TypeAlias = __.cabc.Sequence[ InventoryObject ]
SearchResults: __.typx.TypeAlias = __.cabc.Sequence[ SearchResult ]

