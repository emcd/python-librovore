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
    metadata_lines = obj.render_specifics_markdown( reveal_internals = False )
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