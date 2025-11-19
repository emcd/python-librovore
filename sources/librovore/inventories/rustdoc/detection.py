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


''' Rustdoc inventory detection implementations. '''


from bs4 import BeautifulSoup as _BeautifulSoup

from . import __


# Common "All Items" page paths to probe
_ALL_ITEMS_PATHS = (
    '/all.html',
    '/std/all.html',
)

# Minimum items required for valid Rustdoc inventory
_MINIMUM_ITEM_COUNT = 1
_SUBSTANTIAL_ITEMS_THRESHOLD = 50
_MODERATE_ITEMS_THRESHOLD = 10

# Minimum parts required in "List of all items in" heading
_CRATE_NAME_PARTS_MIN = 4


class RustdocInventoryDetection( __.InventoryDetection ):
    ''' Detection result for Rustdoc inventory sources. '''

    inventory_data: __.Absential[ dict[ str, __.typx.Any ] ] = __.absent

    @classmethod
    async def from_source(
        selfclass,
        auxdata: __.ApplicationGlobals,
        processor: __.Processor,
        source: str,
    ) -> __.typx.Self:
        ''' Constructs Rustdoc inventory detection from source. '''
        base_url = __.normalize_base_url( source )
        inventory_data, confidence = await probe_all_items_page(
            auxdata, base_url )
        return selfclass(
            processor = processor,
            confidence = confidence,
            inventory_data = inventory_data )

    async def filter_inventory(
        self,
        auxdata: __.ApplicationGlobals,
        source: str, /, *,
        filters: __.cabc.Mapping[ str, __.typx.Any ],
    ) -> tuple[ __.InventoryObject, ... ]:
        ''' Filters inventory objects from Rustdoc all items page. '''
        if __.is_absent( self.inventory_data ):
            base_url = __.normalize_base_url( source )
            inventory_data, _ = await probe_all_items_page( auxdata, base_url )
            if __.is_absent( inventory_data ): return tuple( )
        else: inventory_data = self.inventory_data
        objects = filter_inventory(
            inventory_data, source, filters = filters )
        return tuple( objects )


def calculate_confidence(
    items: list[ __.typx.Any ], valid_items: int
) -> float:
    ''' Calculates confidence score based on inventory quality. '''
    if valid_items == 0: return 0.0
    item_ratio = valid_items / len( items ) if items else 0.0
    base_confidence = 0.7
    if valid_items >= _SUBSTANTIAL_ITEMS_THRESHOLD: base_confidence = 0.9
    elif valid_items >= _MODERATE_ITEMS_THRESHOLD: base_confidence = 0.8
    return min( base_confidence * item_ratio, 0.95 )


def filter_inventory(
    inventory_data: dict[ str, __.typx.Any ],
    location_url: str, /, *,
    filters: __.cabc.Mapping[ str, __.typx.Any ],
) -> list[ __.InventoryObject ]:
    ''' Filters inventory objects from parsed Rustdoc data. '''
    items = inventory_data.get( 'items', [ ] )
    item_type_filter = filters.get( 'item_type', '' ) or __.absent
    name_pattern = filters.get( 'name', '' ) or __.absent
    all_objects: list[ __.InventoryObject ] = [ ]
    for item in items:
        if not isinstance( item, dict ): continue
        typed_item = __.typx.cast( dict[ str, __.typx.Any ], item )
        name = str( typed_item.get( 'name', '' ) )
        item_type = str( typed_item.get( 'item_type', '' ) )
        if not name or not item_type: continue
        if (
                not __.is_absent( item_type_filter )
                and item_type_filter != item_type
        ): continue
        if (
                not __.is_absent( name_pattern )
                and name_pattern not in name
        ): continue
        obj = format_inventory_object( typed_item, location_url )
        all_objects.append( obj )
    return all_objects


class RustdocInventoryObject( __.InventoryObject ):
    ''' Rustdoc-specific inventory object with item type information. '''

    def render_specifics_markdown(
        self, /, *,
        reveal_internals: bool = False,
    ) -> tuple[ str, ... ]:
        ''' Renders Rustdoc specifics with item type information. '''
        lines: list[ str ] = [ ]
        role = self.specifics.get( 'role' )
        if role:
            lines.append( f"- **Type:** {role}" )
        if reveal_internals:
            item_type = self.specifics.get( 'item_type' )
            if item_type:
                lines.append( f"- **Item Type:** {item_type}" )
            path = self.specifics.get( 'path' )
            if path:
                lines.append( f"- **Path:** {path}" )
        return tuple( lines )

    def render_specifics_json(
        self, /, *,
        reveal_internals: bool = False,
    ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders Rustdoc specifics with structured item information. '''
        base_data = { 'role': self.specifics.get( 'role' ) }
        if reveal_internals:
            base_data.update( {
                'item_type': self.specifics.get( 'item_type' ),
                'path': self.specifics.get( 'path' ),
                'description': self.specifics.get( 'description' ),
            } )
        return __.immut.Dictionary( base_data )


def format_inventory_object(
    item: dict[ str, __.typx.Any ],
    location_url: str,
) -> RustdocInventoryObject:
    ''' Formats Rustdoc inventory item with complete attribution. '''
    name = str( item.get( 'name', '' ) )
    item_type = str( item.get( 'item_type', '' ) )
    path = str( item.get( 'path', '' ) )
    href = str( item.get( 'href', '' ) )
    description = str( item.get( 'description', '' ) )
    role = _map_item_type_to_role( item_type )
    return RustdocInventoryObject(
        name = name,
        uri = href,
        inventory_type = 'rustdoc',
        location_url = location_url,
        display_name = f"{path}::{name}" if path else name,
        specifics = __.immut.Dictionary(
            item_type = item_type,
            role = role,
            path = path,
            description = description ) )


def _count_valid_items( items: list[ __.typx.Any ] ) -> int:
    ''' Counts valid item entries in all items list. '''
    valid_items = 0
    for item in items:
        if not isinstance( item, dict ): continue
        if 'name' not in item or 'item_type' not in item: continue
        if 'href' not in item: continue
        valid_items += 1
    return valid_items


def _detect_rustdoc_markers( soup: __.typx.Any ) -> bool:
    ''' Detects Rustdoc-specific HTML markers. '''
    meta_generator = soup.find( 'meta', attrs = { 'name': 'generator' } )
    if meta_generator:
        content = meta_generator.get( 'content', '' )
        if 'rustdoc' in str( content ).lower( ):
            return True
    if soup.find( 'rustdoc-topbar' ):
        return True
    if soup.find( attrs = { 'data-rustdoc-version': True } ):
        return True
    css_pattern = __.re.compile( r'rustdoc.*\.css' )
    return bool( soup.find( 'link', href = css_pattern ) )


def _extract_crate_name( soup: __.typx.Any, url_path: str ) -> str:
    ''' Extracts crate name from HTML or URL. '''
    h1 = soup.find( 'h1', class_ = 'fqn' )
    if h1:
        text = h1.get_text( strip = True )
        if text.startswith( 'List of all items in' ):
            parts = text.split( )
            if len( parts ) > _CRATE_NAME_PARTS_MIN:
                return str( parts[ -1 ] )
    path_parts = url_path.strip( '/' ).split( '/' )
    for part in path_parts:
        if part and part != 'all.html':
            return part
    return 'unknown'


def _is_valid_all_items_page( content: str ) -> bool:
    ''' Validates that content is a Rustdoc all items page. '''
    if not content.strip( ): return False
    try: soup = _BeautifulSoup( content, 'lxml' )
    except Exception: return False
    return _detect_rustdoc_markers( soup )


def _map_item_type_to_role( item_type: str ) -> str:
    ''' Maps Rustdoc item types to librovore roles. '''
    type_mapping = {
        'struct': 'type',
        'enum': 'type',
        'trait': 'type',
        'type': 'type',
        'union': 'type',
        'fn': 'function',
        'method': 'method',
        'macro': 'macro',
        'mod': 'module',
        'const': 'constant',
        'static': 'constant',
        'primitive': 'type',
        'keyword': 'keyword',
        'attr': 'attribute',
        'derive': 'attribute',
    }
    return type_mapping.get( item_type, item_type )


def _parse_all_items_page(
    content: str, url_path: str
) -> dict[ str, __.typx.Any ]:
    ''' Parses Rustdoc all items page to extract inventory data. '''
    soup = _BeautifulSoup( content, 'lxml' )
    crate_name = _extract_crate_name( soup, url_path )
    items: list[ dict[ str, __.typx.Any ] ] = [ ]
    item_lists = soup.find_all( 'ul', class_ = 'all-items' )
    for item_list in item_lists:
        section = __.typx.cast( __.typx.Any, item_list.find_previous( 'h2' ) )
        item_type = ''
        if section:
            section_text = str( section.get_text( strip = True ) ).lower( )
            item_type = section_text.rstrip( 's' )
        for li in item_list.find_all( 'li' ):
            link = li.find( 'a' )
            if not link: continue
            href = link.get( 'href', '' )
            name = link.get_text( strip = True )
            description_span = li.find( 'span', class_ = 'desc' )
            description = (
                description_span.get_text( strip = True )
                if description_span else '' )
            path_parts = name.split( '::' )
            if len( path_parts ) > 1:
                path = '::'.join( path_parts[ :-1 ] )
                simple_name = path_parts[ -1 ]
            else:
                path = crate_name
                simple_name = name
            items.append( {
                'name': simple_name,
                'item_type': item_type or 'unknown',
                'path': path,
                'href': href,
                'description': description,
            } )
    return { 'items': items, 'crate': crate_name }


async def probe_all_items_page(
    auxdata: __.ApplicationGlobals,
    base_url: __.typx.Any,
) -> tuple[ __.Absential[ dict[ str, __.typx.Any ] ], float ]:
    ''' Probes for Rustdoc all items page and validates structure. '''
    for path in _ALL_ITEMS_PATHS:
        all_items_url = base_url._replace( path = base_url.path + path )
        result = await _try_single_all_items_page( auxdata, all_items_url )
        if not __.is_absent( result ): return result
    return __.absent, 0.0


async def _try_single_all_items_page(
    auxdata: __.ApplicationGlobals,
    all_items_url: __.typx.Any,
) -> __.Absential[ tuple[ dict[ str, __.typx.Any ], float ] ]:
    ''' Attempts to load and validate a single all items page URL. '''
    all_items_content = await __.retrieve_url_as_text(
        auxdata.content_cache, all_items_url )
    if __.is_absent( all_items_content ):
        return __.absent
    if not _is_valid_all_items_page( all_items_content ):
        return __.absent
    try:
        inventory_data = _parse_all_items_page(
            all_items_content, all_items_url.path )
    except Exception:
        return __.absent
    items = inventory_data.get( 'items', [ ] )
    valid_items = _count_valid_items( items )
    if valid_items < _MINIMUM_ITEM_COUNT:
        return __.absent
    confidence = calculate_confidence( items, valid_items )
    return inventory_data, confidence
