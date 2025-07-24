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


''' Inventory processing and filtering functions. '''


from urllib.parse import ParseResult as _Url

import sphobjinv as _sphobjinv

from . import __


def collect_matching_objects(
    inventory: _sphobjinv.Inventory,
    domain: __.Absential[ str ],
    role: __.Absential[ str ],
    priority: __.Absential[ str ],
    term_matcher: __.cabc.Callable[ [ __.typx.Any ], bool ],
) -> tuple[ dict[ str, __.typx.Any ], int ]:
    ''' Collects objects that match all filters. '''
    objects: __.cabc.MutableMapping[
        str, list[ __.cabc.Mapping[ str, __.typx.Any ] ]
    ] = __.collections.defaultdict(
        list[ __.cabc.Mapping[ str, __.typx.Any ] ] )
    selections_total = 0
    for objct in inventory.objects:
        if domain and objct.domain != domain: continue
        if role and objct.role != role: continue
        if priority and objct.priority != priority: continue
        if not term_matcher( objct ): continue
        objects[ objct.domain ].append( format_inventory_object( objct ) )
        selections_total += 1
    return objects, selections_total


def create_term_matcher(
    term: str,
    match_mode: __.MatchMode
) -> __.cabc.Callable[ [ __.typx.Any ], bool ]:
    ''' Creates a matcher function for term filtering. '''
    if not term: return lambda obj: True
    if match_mode == __.MatchMode.Regex:
        try: pattern = __.re.compile( term, __.re.IGNORECASE )
        except __.re.error as exc:
            message = f"Invalid regex pattern: {term}"
            raise __.InventoryFilterInvalidity( message ) from exc
        return lambda obj: bool( pattern.search( obj.name ) )
    term_lower = term.lower( )
    return lambda obj: term_lower in obj.name.lower( )


def extract_inventory( base_url: _Url ) -> _sphobjinv.Inventory:
    ''' Extracts and parses Sphinx inventory from URL or file path. '''
    from .urls import derive_inventory_url as _derive_inventory_url
    url = _derive_inventory_url( base_url )
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
        raise __.InventoryInaccessibility( url_s, cause = exc ) from exc
    except Exception as exc:
        raise __.InventoryInvalidity( url_s, cause = exc ) from exc


def extract_names_from_suggestions(
    suggestions: list[ str ]
) -> set[ str ]:
    ''' Extracts object names from sphobjinv suggestion format. '''
    fuzzy_names: set[ str ] = set( )
    for suggestion in suggestions:
        if '`' in suggestion:
            name = suggestion.split( '`' )[ 1 ]
            fuzzy_names.add( name )
    return fuzzy_names


def filter_exact_and_regex_matching( # noqa: PLR0913
    inventory: _sphobjinv.Inventory,
    domain: __.Absential[ str ],
    role: __.Absential[ str ],
    priority: __.Absential[ str ],
    term: str,
    match_mode: __.MatchMode,
) -> tuple[ dict[ str, __.typx.Any ], int ]:
    ''' Filters inventory using exact or regex matching. '''
    term_matcher = create_term_matcher( term, match_mode )
    return collect_matching_objects(
        inventory, domain, role, priority, term_matcher )


def filter_fuzzy_matching( # noqa: PLR0913
    inventory: _sphobjinv.Inventory,
    domain: __.Absential[ str ],
    role: __.Absential[ str ],
    priority: __.Absential[ str ],
    term: str,
    fuzzy_threshold: int,
) -> tuple[ dict[ str, __.typx.Any ], int ]:
    ''' Filters inventory using fuzzy matching via sphobjinv.suggest(). '''
    suggestions = inventory.suggest( term, thresh = fuzzy_threshold )
    fuzzy_names = extract_names_from_suggestions( suggestions )
    return collect_matching_objects(
        inventory, domain, role, priority,
        lambda obj: obj.name in fuzzy_names )


def filter_inventory( # noqa: PLR0913
    inventory: _sphobjinv.Inventory,
    domain: __.Absential[ str ] = __.absent,
    role: __.Absential[ str ] = __.absent,
    term: __.Absential[ str ] = __.absent,
    priority: __.Absential[ str ] = __.absent,
    match_mode: __.MatchMode = __.MatchMode.Exact,
    fuzzy_threshold: int = 50,
) -> tuple[ dict[ str, __.typx.Any ], int ]:
    ''' Filters inventory objects by domain, role, term, match mode. '''
    term_ = '' if __.is_absent( term ) else term
    if term_ and match_mode == __.MatchMode.Fuzzy:
        return filter_fuzzy_matching(
            inventory, domain, role, priority, term_, fuzzy_threshold )
    return filter_exact_and_regex_matching(
        inventory, domain, role, priority, term_, match_mode )


def format_inventory_object(
    objct: __.typx.Any
) -> __.cabc.Mapping[ str, __.typx.Any ]:
    ''' Formats an inventory object for output. '''
    return {
        'name': objct.name,
        'role': objct.role,
        'priority': objct.priority,
        'uri': objct.uri,
        'dispname': (
            objct.dispname if objct.dispname != '-' else objct.name
        ),
    }