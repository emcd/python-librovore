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


''' JSON rendering functions for CLI output. '''


from . import __


def render_error_json( result: __.ErrorResponse ) -> str:
    ''' Renders error response as JSON. '''
    serialized = __.serialize_for_json( result )
    return __.json.dumps( serialized, indent = 2 )


def render_detect_result_json( 
    result: dict[ str, __.typx.Any ] | __.ErrorResponse
) -> str:
    ''' Renders detect result as JSON. '''
    if isinstance( result, __.ErrorResponse ):
        return render_error_json( result )
    # TODO: Detection results should be structured objects
    serialized = __.serialize_for_json( result )
    return __.json.dumps( serialized, indent = 2 )


def render_inventory_query_result_json( 
    result: __.InventoryResult
) -> str:
    ''' Renders inventory query result as JSON. '''
    if isinstance( result, __.ErrorResponse ):
        return render_error_json( result )
    serialized = __.serialize_for_json( result )
    return __.json.dumps( serialized, indent = 2 )


def render_content_query_result_json( 
    result: __.ContentResult, lines_max: int = 0
) -> str:
    ''' Renders content query result as JSON. '''
    if isinstance( result, __.ErrorResponse ):
        return render_error_json( result )
    if isinstance( result, __.ContentQueryResult ) and lines_max > 0:
        serialized = __.serialize_for_json( result )
        serialized = _truncate_query_content( serialized, lines_max )
        return __.json.dumps( serialized, indent = 2 )
    serialized = __.serialize_for_json( result )
    return __.json.dumps( serialized, indent = 2 )


def render_inventory_summary_json( 
    result: dict[ str, __.typx.Any ]
) -> str:
    ''' Renders inventory summary as JSON. '''
    serialized = __.serialize_for_json( result )
    return __.json.dumps( serialized, indent = 2 )


def render_survey_processors_json( 
    result: dict[ str, __.typx.Any ]
) -> str:
    ''' Renders survey processors result as JSON. '''
    serialized = __.serialize_for_json( result )
    return __.json.dumps( serialized, indent = 2 )


def _truncate_query_content( 
    serialized: dict[ str, __.typx.Any ], lines_max: int 
) -> dict[ str, __.typx.Any ]:
    ''' Truncates content in serialized query result. '''
    if 'documents' in serialized:
        for doc in serialized[ 'documents' ]:
            if doc.get( 'content' ):
                content_lines = doc[ 'content' ].split( '\n' )
                if len( content_lines ) > lines_max:
                    content_lines = content_lines[ :lines_max ]
                    content_lines.append(
                        "... (truncated at {lines_max} lines)".format(
                            lines_max = lines_max )
                    )
                doc[ 'content' ] = '\n'.join( content_lines )
    return serialized