# vim: set fileencoding=utf-8:
# -*- coding: utf-8 -*-

#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


''' Markdown rendering functions for CLI output. '''


from . import __


def render_error_markdown( 
    result: __.typx.Annotated[
        __.ErrorResponse,
        __.ddoc.Doc( 
            '''Error response containing query context and failure details.'''
        ),
    ]
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( '''Markdown-formatted error display with query context.''' ),
]:
    ''' Renders error response as structured Markdown output. '''
    suggestion_text = (
        "\n\n**Suggestion:** {suggestion}".format( 
            suggestion = result.error.suggestion )
        if result.error.suggestion else "" )
    return """# Error: {title}

**Query:** {query}
**Location:** {location}
**Message:** {message}{suggestion}
""".format(
        title = result.error.title,
        query = result.query,
        location = result.location,
        message = result.error.message,
        suggestion = suggestion_text
    )


def render_detect_result_markdown( 
    result: __.typx.Annotated[
        dict[ str, __.typx.Any ] | __.ErrorResponse,
        __.ddoc.Doc( 
            '''Detection result or error response from processor detection.'''
        ),
    ]
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( 
        '''Markdown-formatted detection results with processor information.'''
    ),
]:
    ''' Renders processor detection results as structured Markdown output. '''
    if isinstance( result, __.ErrorResponse ):
        return render_error_markdown( result )
    # TODO: Detection results should be structured objects
    source = result.get( 'source', 'Unknown' )
    optimal = result.get( 'detection_optimal' )
    time_ms = result.get( 'time_detection_ms', 0 )
    lines = [
        "# Detection Results",
        "**Source:** {source}".format( source = source ),
        "**Detection Time:** {time_ms}ms".format( time_ms = time_ms ),
    ]
    if optimal:
        processor = optimal.get( 'processor', {} )
        confidence = optimal.get( 'confidence', 0 )
        lines.extend([
            "\n## Optimal Processor",
            "- **Name:** {name}".format( 
                name = processor.get( 'name', 'Unknown' ) ),
            "- **Confidence:** {confidence:.1%}".format( 
                confidence = confidence ),
        ])
    return '\n'.join( lines )


def render_inventory_query_result_markdown( 
    result: __.typx.Annotated[
        __.InventoryResult,
        __.ddoc.Doc( 
            '''Inventory query result containing objects or error response.'''
        ),
    ]
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( 
        '''Markdown-formatted inventory results with object details.'''
    ),
]:
    ''' Renders inventory query results as structured Markdown output. '''
    if isinstance( result, __.ErrorResponse ):
        return render_error_markdown( result )
    query = result.query
    objects = result.objects
    metadata = result.search_metadata
    lines = [
        "# Inventory Results: {query}".format( query = query ),
        "**Results:** {results_count}/{matches_total}".format(
            results_count = metadata.results_count,
            matches_total = metadata.matches_total or 0
        ),
    ]
    if objects:
        lines.append( "\n## Objects" )
        for index, obj in enumerate( objects, 1 ):
            separator = "\n\n📦 ── Object {} ─────────────────────── 📦\n"
            lines.append( separator.format( index ) )
            lines.append( "### `{name}`".format( name = obj.name ) )
            _append_inventory_metadata( lines, obj )
    return '\n'.join( lines )


def render_content_query_result_markdown( 
    result: __.typx.Annotated[
        __.ContentResult,
        __.ddoc.Doc( 
            '''Content query result containing documents or error response.'''
        ),
    ],
    lines_max: __.typx.Annotated[
        int,
        __.ddoc.Doc( '''Maximum lines to display per content snippet.''' ),
    ] = 0
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( 
        '''Markdown-formatted content results with document snippets.'''
    ),
]:
    ''' Renders content query results as structured Markdown output. '''
    if isinstance( result, __.ErrorResponse ):
        return render_error_markdown( result )
    if isinstance( result, __.ContentQueryResult ) and lines_max > 0:
        return _format_content_query_result_markdown_truncated( 
            result, lines_max )
    query = result.query
    documents = result.documents
    metadata = result.search_metadata
    lines = [
        "# Query Results: {query}".format( query = query ),
        "**Results:** {results_count}/{matches_total}".format(
            results_count = metadata.results_count,
            matches_total = metadata.matches_total or 0
        ),
    ]
    if documents:
        lines.append( "\n## Documents" )
        for index, doc in enumerate( documents, 1 ):
            separator = "\n\n📄 ── Document {} ──────────────────── 📄\n"
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
                lines.append( "**Content:** {content}".format(
                    content = doc.content_snippet ) )
    return '\n'.join( lines )


def render_inventory_summary_markdown( 
    result: __.typx.Annotated[
        dict[ str, __.typx.Any ],
        __.ddoc.Doc( 
            '''Inventory summary data with project and object information.'''
        ),
    ]
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( 
        '''Markdown-formatted inventory summary with grouped objects.'''
    ),
]:
    ''' Renders inventory summary as structured Markdown output. '''
    has_project = 'project' in result
    has_version = 'version' in result
    has_objects = 'objects' in result
    if has_project and has_version and has_objects:
        lines = [
            "# {project}".format( project = result[ 'project' ] ),
            "**Version:** {version}".format( version = result[ 'version' ] ),
            "**Objects:** {objects_count}".format( 
                objects_count = result[ 'objects_count' ] ),
        ]
        objects_value = result.get( 'objects' )
        if objects_value:
            if isinstance( objects_value, dict ):
                grouped_objects = __.typx.cast(
                    __.cabc.Mapping[ str, __.typx.Any ], objects_value )
                lines.extend( _format_grouped_objects( grouped_objects ) )
            else:
                lines.extend( _format_object_list( objects_value ) )
        return '\n'.join( lines )
    # TODO: Remove fallback once working with proper objects instead of dicts
    return __.json.dumps( result, indent = 2 )


def render_survey_processors_markdown( 
    result: __.typx.Annotated[
        dict[ str, __.typx.Any ],
        __.ddoc.Doc( 
            '''Processor survey results with available processors.'''
        ),
    ]
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( '''JSON-formatted processor survey information.''' ),
]:
    ''' Renders processor survey results as JSON output. '''
    serialized = __.serialize_for_json( result )
    return __.json.dumps( serialized, indent = 2 )


def _format_content_query_result_markdown_truncated(
    result: __.typx.Annotated[
        __.ContentQueryResult,
        __.ddoc.Doc( '''Content query result with documents to format.''' ),
    ], 
    lines_max: __.typx.Annotated[
        int,
        __.ddoc.Doc( '''Maximum lines to display per content snippet.''' ),
    ]
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( 
        '''Truncated Markdown content with line limit indicators.'''
    ),
]:
    ''' 
    Formats content query results as Markdown with truncated content snippets. 
    '''
    query = result.query
    documents = result.documents
    metadata = result.search_metadata
    lines = [
        "# Query Results: {query} (truncated)".format( query = query ),
        "**Results:** {results_count}/{matches_total}".format(
            results_count = metadata.results_count,
            matches_total = metadata.matches_total or 0
        ),
    ]
    if documents:
        lines.append( "\n## Documents" )
        for index, doc in enumerate( documents, 1 ):
            separator = "\n\n📄 ── Document {} ──────────────────── 📄\n"
            lines.append( separator.format( index ) )
            lines.append( "**URL:** {url}".format(
                url = doc.documentation_url ) )
            if doc.signature:
                lines.append( "**Signature:** {signature}".format(
                    signature = doc.signature ) )
            if doc.content_snippet:
                content_lines = doc.content_snippet.split( '\n' )
                if len( content_lines ) > lines_max:
                    content_lines = content_lines[ :lines_max ]
                    content_lines.append(
                        "... (truncated at {lines_max} lines)".format(
                            lines_max = lines_max )
                    )
                lines.append( "**Content:** {content}".format(
                    content = '\n'.join( content_lines ) ) )
    return '\n'.join( lines )


def _append_inventory_metadata(
    lines: __.typx.Annotated[
        list[ str ],
        __.ddoc.Doc( 
            '''Markdown lines list to extend with object metadata.'''
        ),
    ], 
    obj: __.typx.Annotated[
        __.InventoryObject,
        __.ddoc.Doc( 
            '''Inventory object with self-rendering capabilities.'''
        ),
    ]
) -> None:
    ''' Appends inventory object metadata using self-rendering interface. '''
    metadata_lines = obj.render_specifics_markdown( show_technical = False )
    lines.extend( metadata_lines )


def _format_grouped_objects(
    grouped_objects: __.typx.Annotated[
        __.cabc.Mapping[ str, __.typx.Any ],
        __.ddoc.Doc( '''Objects grouped by category with mixed types.''' ),
    ]
) -> __.typx.Annotated[
    list[ str ],
    __.ddoc.Doc( '''Markdown lines with formatted object groups.''' ),
]:
    '''
    Formats grouped objects for Markdown display with type-safe object access.
    '''
    lines: list[ str ] = []
    for group_name, group_objects in grouped_objects.items():
        lines.extend([
            "\n## {group_name}".format( group_name = group_name ),
            "Objects: {count}".format( count = len( group_objects ) ),
        ])
        object_names = [
            "- {name}".format( name = _extract_object_name( obj ) )
            for obj in group_objects
        ]
        lines.extend( object_names )
    return lines


def _format_object_list( 
    objects: __.typx.Annotated[
        __.typx.Any,
        __.ddoc.Doc( 
            '''Mixed sequence of objects with varying name access patterns.'''
        ),
    ]
) -> __.typx.Annotated[
    list[ str ],
    __.ddoc.Doc( '''Markdown bullet list of object names.''' ),
]:
    '''
    Formats object list for Markdown display with type-safe name extraction.
    '''
    lines: list[ str ] = []
    if not hasattr( objects, '__len__' ): return lines
    for obj in objects:
        object_name = _extract_object_name( obj )
        lines.append( "- {name}".format( name = object_name ) )
    return lines


def _extract_object_name( 
    obj: __.typx.Annotated[
        __.typx.Any,
        __.ddoc.Doc( '''Object with various name access patterns.''' ),
    ]
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( '''Extracted object name or fallback representation.''' ),
]:
    ''' 
    Extracts object name with type-safe handling of different object types. 
    '''
    if hasattr( obj, 'name' ):
        return str( obj.name )
    if isinstance( obj, dict ):
        dict_obj = __.typx.cast( dict[ str, __.typx.Any ], obj )
        name_value = dict_obj.get( 'name', 'Unknown' )
        return str( name_value )
    return str( obj )