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


import urllib.parse as _urlparse

import sphobjinv as _sphobjinv

from . import __
from . import exceptions as _exceptions


def extract_inventory(
    source: str,
    *,
    domain: str | None = None,
    role: str | None = None,
    search: str | None = None
) -> dict[ str, __.typx.Any ]:
    ''' Extracts Sphinx inventory from URL or file path with optional
    filtering. '''
    # Normalize source to ensure it points to objects.inv
    normalized_source = _normalize_inventory_source( source )
    # Determine if source is URL or file path
    if _is_url( normalized_source ):
        try:
            inventory = _sphobjinv.Inventory( url = normalized_source )
        except ( OSError, ConnectionError, TimeoutError ) as exc:
            raise _exceptions.NetworkConnectionFailure(
                normalized_source
            ) from exc
        except Exception as exc:
            raise _exceptions.InventoryFormatInvalidity(
                normalized_source
            ) from exc
    else:
        path = __.Path( normalized_source ).resolve( )
        inventory = _load_local_inventory( path )
    objects_by_domain: dict[ str, list[ dict[ str, __.typx.Any ] ] ] = { }
    total_filtered = 0
    for obj in inventory.objects:
        # Apply filtering during iteration
        if domain and obj.domain != domain:
            continue
        if role and obj.role != role:
            continue
        if search and search.lower( ) not in obj.name.lower( ):
            continue
        # Object passes filters, add to results
        domain_name: str = obj.domain
        if domain_name not in objects_by_domain:
            objects_by_domain[ domain_name ] = [ ]
        objects_by_domain[ domain_name ].append( {
            'name': obj.name,
            'role': obj.role,
            'priority': obj.priority,
            'uri': obj.uri,
            'dispname': obj.dispname if obj.dispname != '-' else obj.name,
        } )
        total_filtered += 1
    domains_summary: dict[ str, int ] = {
        domain_name: len( objs )
        for domain_name, objs in objects_by_domain.items( )
    }
    result: dict[ str, __.typx.Any ] = {
        'project': inventory.project,
        'version': inventory.version,
        'source': source,
        'object_count': total_filtered,
        'domains': domains_summary,
        'objects': objects_by_domain,
    }
    # Add filters field if any filters were applied
    if any( [ domain, role, search ] ):
        result[ 'filters' ] = {
            'domain': domain,
            'role': role,
            'search': search,
        }
    return result


def hello( name: str ) -> str:
    ''' Says hello. '''
    return f"Hello, {name}!"




def summarize_inventory( 
    source: str, 
    *, 
    filters: dict[ str, str | None ] | None = None 
) -> str:
    ''' Provides human-readable summary of a Sphinx inventory. '''
    data = extract_inventory( source )
    lines = [
        "Sphinx Inventory: {project} v{version}".format(
            project = data[ 'project' ], version = data[ 'version' ]
        ),
        "Source: {source}".format( source = data[ 'source' ] ),
        "Total Objects: {count}".format( count = data[ 'object_count' ] ),
    ]
    # Show filter information if present
    if filters and any( filters.values( ) ):
        filter_parts: list[ str ] = [ ]
        for filter_name, filter_value in filters.items( ):
            if filter_value:
                filter_parts.append( "{name}={value}".format(
                    name = filter_name, value = filter_value ) )
        if filter_parts:
            lines.append( "Filters: {parts}".format(
                parts = ', '.join( filter_parts ) ) )
    lines.extend( [ "", "Domains:" ] )
    for domain, count in sorted( data[ 'domains' ].items( ) ):
        lines.append( "  {domain}: {count} objects".format(
            domain = domain, count = count ) )
    # Show sample objects from largest domain
    if data[ 'objects' ]:
        largest_domain = max(
            data[ 'domains' ].items( ), key = lambda x: x[ 1 ] )[ 0 ]
        sample_objects = data[ 'objects' ][ largest_domain ][ :5 ]
        lines.extend( [
            "",
            "Sample {domain} objects:".format( domain = largest_domain ),
        ] )
        lines.extend(
            "  {role}: {name}".format(
                role = obj[ 'role' ], name = obj[ 'name' ] )
            for obj in sample_objects )
    return '\n'.join( lines )


def _load_local_inventory( path: __.Path ) -> _sphobjinv.Inventory:
    ''' Loads inventory from local file path. '''
    if not path.exists( ):
        raise _exceptions.InventoryAbsence(
            str( path ), "Inventory file not found"
        )
    try:
        return _sphobjinv.Inventory( fname_zlib = str( path ) )
    except Exception as exc:
        raise _exceptions.InventoryFormatInvalidity( str( path ) ) from exc


def _normalize_inventory_source( source: str ) -> str:
    ''' Appends objects.inv to URLs and paths that don't already have it. '''
    if source.endswith( 'objects.inv' ): return source
    if _is_url( source ):
        try:
            parsed = _urlparse.urlparse( source )
            path = parsed.path.rstrip( '/' ) + '/objects.inv'
            return _urlparse.urlunparse( parsed._replace( path = path ) )
        except Exception as exc:
            raise _exceptions.InventoryUrlInvalidity(
                source, "Failed to parse URL" ) from exc
    else:
        path = __.Path( source )
        if path.is_dir( ) or not path.suffix:
            return str( path / 'objects.inv' )
        return source


def _is_url( source: str ) -> bool:
    ''' Determines if source is a URL using urlparse. '''
    try:
        parsed = _urlparse.urlparse( source )
    except Exception:
        return False
    else:
        return parsed.scheme in ( 'http', 'https', 'file' )
