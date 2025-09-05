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


''' Centralized search engine for universal matching across processors. '''


import re as _re

import rapidfuzz as _rapidfuzz

from . import __
from . import interfaces as _interfaces
from . import results as _results


_SEARCH_BEHAVIORS_DEFAULT = _interfaces.SearchBehaviors( )
_EXACT_THRESHOLD_MIN = 95


def filter_by_name(
    objects: __.cabc.Sequence[ _results.InventoryObject ],
    term: str, /, *,
    search_behaviors: _interfaces.SearchBehaviors = _SEARCH_BEHAVIORS_DEFAULT,
) -> tuple[ _results.SearchResult, ... ]:
    ''' Filters objects by name using specified match mode and options. '''
    if not term:
        return tuple(
            _results.SearchResult.from_inventory_object(
                obj, score = 1.0, match_reasons = [ 'empty term' ] )
            for obj in objects
        )

    results: list[ _results.SearchResult ] = [ ]

    match search_behaviors.match_mode:
        case _interfaces.MatchMode.Exact:
            results = _filter_exact(
                objects, term, search_behaviors.contains_term,
                search_behaviors.case_sensitive )
        case _interfaces.MatchMode.Pattern:
            results = _filter_regex( objects, term )
        case _interfaces.MatchMode.Similar:
            results = _filter_similar(
                objects, term, search_behaviors.similarity_score_min,
                search_behaviors.contains_term,
                search_behaviors.case_sensitive )

    sorted_results = sorted( results, key = lambda r: r.score, reverse = True )
    return tuple( sorted_results )


def _filter_exact(
    objects: __.cabc.Sequence[ _results.InventoryObject ],
    term: str,
    contains_term: bool,
    case_sensitive: bool
) -> list[ _results.SearchResult ]:
    ''' Applies exact matching with partial_ratio for precision discovery. '''
    results: list[ _results.SearchResult ] = [ ]
    term_compare = term if case_sensitive else term.lower( )
    for obj in objects:
        obj_name_compare = obj.name if case_sensitive else obj.name.lower( )
        if obj_name_compare == term_compare:
            score = 1.0
            reason = 'exact match'
        elif contains_term:
            partial_score = _rapidfuzz.fuzz.partial_ratio(
                term_compare, obj_name_compare )
            if partial_score >= _EXACT_THRESHOLD_MIN:
                score = partial_score / 100.0
                reason = f'partial match ({partial_score}%)'
            else:
                continue
        else:
            continue
        results.append( _results.SearchResult.from_inventory_object(
            obj, score = score, match_reasons = [ reason ] ) )
    return results


def _filter_regex(
    objects: __.cabc.Sequence[ _results.InventoryObject ],
    query: str
) -> list[ _results.SearchResult ]:
    ''' Apply regex matching to objects. '''
    try:
        pattern = _re.compile( query, _re.IGNORECASE )
    except _re.error:
        return [ ]

    return [
        _results.SearchResult.from_inventory_object(
            obj, score = 1.0, match_reasons = [ 'regex match' ] )
        for obj in objects if pattern.search( obj.name )
    ]


def _filter_similar(
    objects: __.cabc.Sequence[ _results.InventoryObject ],
    term: str,
    similarity_score_min: int,
    contains_term: bool,
    case_sensitive: bool
) -> list[ _results.SearchResult ]:
    ''' Applies similar matching with partial_ratio for discovery. '''
    results: list[ _results.SearchResult ] = [ ]
    term_compare = term if case_sensitive else term.lower( )
    for obj in objects:
        obj_name_compare = obj.name if case_sensitive else obj.name.lower( )
        if obj_name_compare == term_compare:
            score = 1.0
            reason = 'exact match'
        elif contains_term:
            partial_score = _rapidfuzz.fuzz.partial_ratio(
                term_compare, obj_name_compare )
            regular_score = _rapidfuzz.fuzz.ratio(
                term_compare, obj_name_compare )
            ratio = max( partial_score, regular_score )
            if ratio >= similarity_score_min:
                score = ratio / 100.0
                score_type = ( 'partial' if partial_score > regular_score 
                              else 'similar' )
                reason = f'{score_type} match ({ratio}%)'
            else:
                continue
        else:
            continue
        results.append( _results.SearchResult.from_inventory_object(
            obj, score = score, match_reasons = [ reason ] ) )
    return results
