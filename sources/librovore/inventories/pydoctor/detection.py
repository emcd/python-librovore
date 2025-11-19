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


''' Inventory detection implementations. '''


from json import loads as _json_loads
from urllib.parse import ParseResult as _Url

from . import __


class PydoctorInventoryDetection( __.InventoryDetection ):
    ''' Detection result for Pydoctor inventory sources. '''

    @classmethod
    async def from_source(
        selfclass,
        auxdata: __.ApplicationGlobals,
        processor: __.Processor,
        source: str,
    ) -> __.typx.Self:
        ''' Constructs Pydoctor inventory detection from source. '''
        return selfclass( processor = processor, confidence = 0.0 )

    async def filter_inventory(
        self,
        auxdata: __.ApplicationGlobals,
        source: str, /, *,
        filters: __.cabc.Mapping[ str, __.typx.Any ],
    ) -> tuple[ __.InventoryObject, ... ]:
        ''' Filters inventory objects from Pydoctor source. '''
        objects = await filter_inventory(
            auxdata, source, filters = filters )
        return tuple( objects )


def derive_searchindex_url( base_url: _Url ) -> _Url:
    ''' Derives searchindex.json URL from base URL ParseResult. '''
    new_path = f"{base_url.path}/searchindex.json"
    return base_url._replace( path = new_path )


async def check_searchindex(
    auxdata: __.ApplicationGlobals, base_url: _Url
) -> bool:
    ''' Checks if searchindex.json exists at source for detection. '''
    searchindex_url = derive_searchindex_url( base_url )
    try:
        return await __.probe_url( auxdata.probe_cache, searchindex_url )
    except Exception: return False


def extract_searchindex( base_url: _Url, content: bytes ) -> __.typx.Any:
    ''' Parses Pydoctor searchindex.json content. '''
    url_s = base_url.geturl( )
    try:
        return _json_loads( content.decode( 'utf-8' ) )
    except ( ValueError, UnicodeDecodeError ) as exc:
        raise __.InventoryInvalidity( url_s, cause = exc ) from exc


def infer_object_type( qname: str ) -> str:
    ''' Infers object type from qualified name using naming conventions.

        Object type is inferred from naming conventions:
        - Capitalized name after last dot: likely a class
        - Lowercase name after last dot: likely a function/method
        - No dots: likely a module
    '''
    if '.' not in qname:
        return 'module'
    parts = qname.rsplit( '.', 1 )
    name = parts[ 1 ]
    if name and name[ 0 ].isupper( ):
        return 'class'
    return 'function'


async def filter_inventory(
    auxdata: __.ApplicationGlobals,
    source: str, /, *,
    filters: __.cabc.Mapping[ str, __.typx.Any ],
) -> tuple[ __.InventoryObject, ... ]:
    ''' Extracts and filters inventory objects from Pydoctor searchindex. '''
    object_type_filter = filters.get( 'type', '' ) or __.absent
    base_url = __.normalize_base_url( source )
    searchindex_url = derive_searchindex_url( base_url )
    try:
        content = await __.retrieve_url(
            auxdata.content_cache, searchindex_url )
    except ( ConnectionError, OSError, TimeoutError ) as exc:
        raise __.InventoryInaccessibility(
            searchindex_url.geturl( ), cause = exc ) from exc
    searchindex = extract_searchindex( base_url, content )
    all_objects: list[ __.InventoryObject ] = [ ]
    field_vectors: __.typx.Any = searchindex.get( 'fieldVectors', [ ] )
    field_entry: __.typx.Any
    for field_entry in field_vectors:
        if not isinstance( field_entry, list ):
            continue
        if len( field_entry ) < 1:  # pyright: ignore[reportUnknownArgumentType]
            continue
        field_name: __.typx.Any = field_entry[ 0 ]  # pyright: ignore[reportUnknownVariableType]
        if not isinstance( field_name, str ):
            continue
        if not field_name.startswith( 'qname/' ):
            continue
        qname = field_name[ 6: ]
        if not qname:
            continue
        object_type = infer_object_type( qname )
        if (
            not __.is_absent( object_type_filter ) and
            object_type != object_type_filter
        ):
            continue
        obj = format_inventory_object(
            qname, object_type, searchindex, source )
        all_objects.append( obj )
    return tuple( all_objects )


class PydoctorInventoryObject( __.InventoryObject ):
    ''' Pydoctor-specific inventory object with type information. '''

    def render_specifics_markdown(
        self, /, *,
        reveal_internals: bool = False,
    ) -> tuple[ str, ... ]:
        ''' Renders Pydoctor specifics with type information. '''
        lines: list[ str ] = [ ]
        object_type = self.specifics.get( 'type' )
        if object_type:
            lines.append( f"- **Type:** {object_type}" )
        if reveal_internals:
            qualified_name = self.specifics.get( 'qualified_name' )
            if qualified_name:
                lines.append( f"- **Qualified Name:** {qualified_name}" )
            version = self.specifics.get( 'searchindex_version' )
            if version:
                lines.append( f"- **Index Version:** {version}" )
        return tuple( lines )

    def render_specifics_json(
        self, /, *,
        reveal_internals: bool = False,
    ) -> __.immut.Dictionary[ str, __.typx.Any ]:
        ''' Renders Pydoctor specifics with structured format. '''
        base_data = { 'type': self.specifics.get( 'type' ) }
        if reveal_internals:
            base_data.update( {
                'qualified_name': self.specifics.get( 'qualified_name' ),
                'searchindex_version': self.specifics.get(
                    'searchindex_version' ),
            } )
        return __.immut.Dictionary( base_data )


def format_inventory_object(
    qname: str,
    object_type: str,
    searchindex: __.typx.Any,
    location_url: str,
) -> PydoctorInventoryObject:
    ''' Formats Pydoctor inventory object with complete attribution. '''
    uri = qname.replace( '.', '/' ) + '.html'
    return PydoctorInventoryObject(
        name = qname,
        uri = uri,
        inventory_type = 'pydoctor',
        location_url = location_url,
        display_name = None,
        specifics = __.immut.Dictionary(
            type = object_type,
            qualified_name = qname,
            searchindex_version = searchindex.get( 'version' ) ) )
