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


''' Core business logic shared between CLI and MCP server. '''

import sphobjinv as _sphobjinv

from . import __


def extract_inventory( source: str ) -> dict[ str, __.typx.Any ]:
    # TODO: Use 'urllib.parse.urlparse'.
    ''' Extracts Sphinx inventory from URL or file path. '''
    # Determine if source is URL or file path
    if source.startswith( ( 'http://', 'https://', 'file://' ) ):
        inventory = _sphobjinv.Inventory( url = source )
    else:
        path = __.Path( source ).resolve( )
        inventory = _load_local_inventory( path )
    objects_by_domain = { }
    for obj in inventory.objects:
        domain = obj.domain
        if domain not in objects_by_domain:
            objects_by_domain[ domain ] = [ ]
        objects_by_domain[ domain ].append( {
            'name': obj.name,
            'role': obj.role,
            'priority': obj.priority,
            'uri': obj.uri,
            'dispname': obj.dispname if obj.dispname != '-' else obj.name,
        } )
    domains_summary = {
        domain: len( objs ) for domain, objs in objects_by_domain.items( )
    }
    return {
        'project': inventory.project,
        'version': inventory.version,
        'source': source,
        'object_count': len( inventory.objects ),
        'domains': domains_summary,
        'objects': objects_by_domain,
    }


def hello( name: str ) -> str:
    ''' Says hello. '''
    return f"Hello, {name}!"


def summarize_inventory( source: str ) -> str:
    ''' Provides human-readable summary of a Sphinx inventory. '''
    data = extract_inventory( source )
    lines = [
        f"Sphinx Inventory: {data['project']} v{data['version']}",
        f"Source: {data['source']}",
        f"Total Objects: {data['object_count']}",
        "",
        "Domains:",
    ]
    for domain, count in sorted( data['domains'].items( ) ):
        lines.append( f"  {domain}: {count} objects" )
    # Show sample objects from largest domain
    if data['objects']:
        largest_domain = max(
            data['domains'].items( ), key = lambda x: x[1]
        )[0]
        sample_objects = data['objects'][largest_domain][:5]
        lines.extend( [
            "",
            f"Sample {largest_domain} objects:",
        ] )
        lines.extend(
            f"  {obj['role']}: {obj['name']}" for obj in sample_objects
        )
    return "\n".join( lines )


def _load_local_inventory( path: __.Path ) -> _sphobjinv.Inventory:
    ''' Loads inventory from local file path. '''
    if not path.exists( ):
        raise FileNotFoundError
    return _sphobjinv.Inventory( fname_zlib = str( path ) )
