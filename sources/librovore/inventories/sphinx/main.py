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


from urllib.parse import ParseResult as _Url

import sphobjinv as _sphobjinv

from . import __
from . import detection as _detection


def derive_inventory_url( base_url: _Url ) -> _Url:
    ''' Derives objects.inv URL from base URL ParseResult. '''
    new_path = f"{base_url.path}/objects.inv"
    return base_url._replace( path = new_path )


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


async def check_objects_inv( base_url: __.typx.Any ) -> bool:
    ''' Checks if objects.inv exists at the source for inventory detection. '''
    try:
        inventory_url = derive_inventory_url( base_url )
        return await __.probe_url( inventory_url )
    except Exception:
        return False


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
    base_url = __.normalize_base_url( source )
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


class SphinxInventoryProcessor( __.InventoryProcessor ):
    ''' Processes Sphinx inventory files (objects.inv format). '''

    name: str = 'sphinx'

    @property
    def capabilities( self ) -> __.ProcessorCapabilities:
        ''' Returns Sphinx inventory processor capabilities. '''
        return __.ProcessorCapabilities(
            processor_name = 'sphinx',
            version = '1.0.0',
            supported_filters = [
                __.FilterCapability(
                    name = 'domain',
                    description = 'Filter by object domain (e.g., py, js)',
                    type = 'string'
                ),
                __.FilterCapability(
                    name = 'role',
                    description = 'Filter by object role (e.g., class, func)',
                    type = 'string'
                ),
                __.FilterCapability(
                    name = 'priority',
                    description = 'Filter by object priority',
                    type = 'string'
                ),
            ],
            results_limit_max = 10000,
            response_time_typical = 'fast',
            notes = 'Processes Sphinx inventory files (objects.inv format)'
        )

    async def detect( self, source: str ) -> __.InventoryDetection:
        ''' Detects if source has a Sphinx inventory file. '''
        try:
            # Try to derive inventory URL and check if it exists
            base_url = __.normalize_base_url( source )
            inventory_url = derive_inventory_url( base_url )
            # For now, basic confidence based on URL structure
            confidence = 0.9 if 'objects.inv' in str( inventory_url ) else 0.1
            # TODO: Actually probe the URL to check if inventory exists
            return _detection.SphinxInventoryDetection(
                processor = self,
                confidence = confidence
            )
        except Exception:
            return _detection.SphinxInventoryDetection(
                processor = self,
                confidence = 0.0
            )

    async def filter_inventory(
        self, source: str, /, *,
        filters: __.cabc.Mapping[ str, __.typx.Any ],
        details: __.InventoryQueryDetails = (
            __.InventoryQueryDetails.Documentation ),
    ) -> list[ dict[ str, __.typx.Any ] ]:
        ''' Extracts and filters inventory objects from source. '''
        return await filter_inventory(
            source, filters = filters, details = details )
