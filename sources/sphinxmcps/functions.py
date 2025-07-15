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
    source: str, /, *,
    domain: __.Absential[ str ] = __.absent,
    role: __.Absential[ str ] = __.absent,
    term: __.Absential[ str ] = __.absent,
) -> dict[ str, __.typx.Any ]:
    ''' Extracts Sphinx inventory from source with optional filtering. '''
    inventory = _extract_inventory( source )
    objects, selections_total = (
        _filter_inventory(
            inventory, domain = domain, role = role, term = term ) )
    domains_summary: dict[ str, int ] = {
        domain_name: len( objs )
        for domain_name, objs in objects.items( )
    }
    result: dict[ str, __.typx.Any ] = {
        'project': inventory.project,
        'version': inventory.version,
        'source': source,
        'object_count': selections_total,
        'domains': domains_summary,
        'objects': objects,
    }
    if any( ( domain, role, term ) ):
        result[ 'filters' ] = { }
        if not __.is_absent( domain ):
            result[ 'filters' ][ 'domain' ] = domain
        if not __.is_absent( role ):
            result[ 'filters' ][ 'role' ] = role
        if not __.is_absent( term ):
            result[ 'filters' ][ 'term' ] = term
    return result


def summarize_inventory(
    source: str, /, *,
    domain: __.Absential[ str ] = __.absent,
    role: __.Absential[ str ] = __.absent,
    term: __.Absential[ str ] = __.absent,
) -> str:
    ''' Provides human-readable summary of a Sphinx inventory. '''
    data = extract_inventory(
        source, domain = domain, role = role, term = term )
    lines = [
        "Sphinx Inventory: {project} v{version}".format(
            project = data[ 'project' ], version = data[ 'version' ]
        ),
        "Source: {source}".format( source = data[ 'source' ] ),
        "Total Objects: {count}".format( count = data[ 'object_count' ] ),
    ]
    filters = data.get( 'filters' )
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
    for domain_, count in sorted( data[ 'domains' ].items( ) ):
        lines.append( "  {domain}: {count} objects".format(
            domain = domain_, count = count ) )
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


def _extract_inventory( source: str ) -> _sphobjinv.Inventory:
    url = _normalize_inventory_source( source )
    url_s = _urlparse.urlunparse( url )
    nomargs: __.NominativeArguments = { }
    match url.scheme:
        case 'http' | 'https': nomargs[ 'url' ] = url_s
        case 'file' | '': nomargs[ 'fname_zlib' ] = url_s
        case _:
            raise _exceptions.InventoryUrlNoSupport(
                url, component = 'scheme', value = url.scheme )
    try: return _sphobjinv.Inventory( **nomargs )
    except ( ConnectionError, OSError, TimeoutError ) as exc:
        raise _exceptions.InventoryInaccessibility(
            url_s, cause = exc ) from exc
    except Exception as exc:
        raise _exceptions.InventoryInvalidity(
            url_s, cause = exc ) from exc


def _filter_inventory(
    inventory: _sphobjinv.Inventory,
    domain: __.Absential[ str ] = __.absent,
    role: __.Absential[ str ] = __.absent,
    term: __.Absential[ str ] = __.absent,
) -> tuple[ dict[ str, __.typx.Any ], int ]:
    objects: __.cabc.MutableMapping[
        str, list[ __.cabc.Mapping[ str, __.typx.Any ] ]
    ] = __.collections.defaultdict(
        list[ __.cabc.Mapping[ str, __.typx.Any ] ] )
    selections_total = 0
    term_ = '' if __.is_absent( term ) else term.lower( )
    for objct in inventory.objects:
        if domain and objct.domain != domain: continue
        if role and objct.role != role: continue
        if term_ and term_ not in objct.name.lower( ): continue
        objects[ objct.domain ].append( {
            'name': objct.name,
            'role': objct.role,
            'priority': objct.priority,
            'uri': objct.uri,
            'dispname':
                objct.dispname if objct.dispname != '-' else objct.name,
        } )
        selections_total += 1
    return objects, selections_total


def _normalize_inventory_source( source: str ) -> _urlparse.ParseResult:
    ''' Parses URL strings into components.

        Also appends 'objects.inv' to the path component, if necessary.
    '''
    try: url = _urlparse.urlparse( source )
    except Exception as exc:
        raise _exceptions.InventoryUrlInvalidity( source ) from exc
    filename = 'objects.inv'
    if url.path.endswith( filename ): return url
    return _urlparse.ParseResult(
        scheme = url.scheme, netloc = url.netloc,
        path = f"{url.path}/{filename}",
        params = url.params, query = url.query, fragment = url.fragment )
