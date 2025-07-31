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


''' Sphinx inventory processor for objects.inv format. '''


import urllib.parse as _urlparse
from urllib.parse import ParseResult as _Url

import sphobjinv as _sphobjinv

from . import __


def derive_inventory_url( base_url: _Url ) -> _Url:
    ''' Derives objects.inv URL from base URL ParseResult. '''
    new_path = f"{base_url.path}/objects.inv"
    return base_url._replace( path = new_path )


def normalize_base_url( source: str ) -> _Url:
    ''' Extracts clean base documentation URL from any source. '''
    try: url = _urlparse.urlparse( source )
    except Exception as exc:
        raise __.InventoryUrlInvalidity( source ) from exc
    match url.scheme:
        case '':
            path = __.Path( source )
            if path.is_file( ) or ( not path.exists( ) and path.suffix ):
                path = path.parent
            url = _urlparse.urlparse( path.resolve( ).as_uri( ) )
        case 'http' | 'https' | 'file': pass
        case _:
            raise __.InventoryUrlNoSupport(
                url, component = 'scheme', value = url.scheme )
    # Remove trailing slash for consistency
    path = url.path.rstrip( '/' ) if url.path != '/' else ''
    return url._replace( path = path )


def extract_inventory( base_url: _Url ) -> _sphobjinv.Inventory:
    ''' Extracts and parses Sphinx inventory from URL or file path. '''
    url = derive_inventory_url( base_url )
    url_s = url.geturl( )
    nomargs: __.NominativeArguments = { }
    match url.scheme:
        case 'http' | 'https': nomargs[ 'url' ] = url_s
        case 'file': nomargs[ 'fname_zlib' ] = url.path
        case _:
            raise __.InventoryUrlNoSupport(
                url, component = 'scheme', value = url.scheme )
    try: return _sphobjinv.Inventory( **nomargs )
    except ( ConnectionError, OSError, TimeoutError ) as exc:
        raise __.InventoryInaccessibility(
            url_s, cause = exc ) from exc
    except Exception as exc:
        raise __.InventoryInvalidity( url_s, cause = exc ) from exc


async def filter_inventory(
    source: str, /, *,
    filters: __.cabc.Mapping[ str, __.typx.Any ],
    details: __.InventoryQueryDetails = (
        __.InventoryQueryDetails.Documentation ),
) -> list[ dict[ str, __.typx.Any ] ]:
    ''' Extracts and filters inventory objects by structural criteria only. '''
    domain = filters.get( 'domain', '' ) or __.absent
    role = filters.get( 'role', '' ) or __.absent
    priority = filters.get( 'priority', '' ) or __.absent
    base_url = normalize_base_url( source )
    inventory = extract_inventory( base_url )
    all_objects: list[ dict[ str, __.typx.Any ] ] = [ ]
    for objct in inventory.objects:
        if not __.is_absent( domain ) and objct.domain != domain: continue
        if not __.is_absent( role ) and objct.role != role: continue
        if not __.is_absent( priority ) and objct.priority != priority:
            continue
        obj = dict( format_inventory_object( objct ) )
        obj[ '_inventory_project' ] = inventory.project
        obj[ '_inventory_version' ] = inventory.version
        all_objects.append( obj )
    return all_objects


def format_inventory_object(
    objct: __.typx.Any,
) -> __.cabc.Mapping[ str, __.typx.Any ]:
    ''' Formats an inventory object for output. '''
    return {
        'name': objct.name,
        'domain': objct.domain,
        'role': objct.role,
        'priority': objct.priority,
        'uri': objct.uri,
        'dispname': (
            objct.dispname if objct.dispname != '-' else objct.name
        ),
    }


class SphinxInventoryProcessor( __.immut.DataclassObject ):
    ''' Processes Sphinx inventory files (objects.inv format). '''

    async def filter_inventory(
        self, source: str, /, *,
        filters: __.cabc.Mapping[ str, __.typx.Any ],
        details: __.InventoryQueryDetails = (
            __.InventoryQueryDetails.Documentation ),
    ) -> list[ dict[ str, __.typx.Any ] ]:
        ''' Extracts and filters inventory objects from source. '''
        return await filter_inventory(
            source, filters = filters, details = details )
