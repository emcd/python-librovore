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
#  WITHOUT WARRANTIES OR CONDITIONS of ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Main Sphinx processor implementation. '''


from . import __
from . import conversion as _conversion
from . import detection as _detection
from . import extraction as _extraction
from . import inventory as _inventory
from . import urls as _urls


_scribe = __.acquire_scribe( __name__ )
_search_behaviors_default = __.SearchBehaviors( )
_filters_default = __.immut.Dictionary[ str, __.typx.Any ]( )


class SphinxProcessor( __.Processor ):
    ''' Processor for Sphinx documentation sources. '''

    name: str = 'sphinx'

    @property
    def capabilities( self ) -> __.ProcessorCapabilities:
        ''' Returns Sphinx processor capabilities. '''
        return __.ProcessorCapabilities(
            processor_name = 'sphinx',
            version = '1.0.0',
            supported_filters = [
                __.FilterCapability(
                    name = 'domain',
                    description = 'Sphinx domain (py, std, js, etc.)',
                    type = 'string',
                    values = None,
                ),
                __.FilterCapability(
                    name = 'role',
                    description = 'Object role (class, function, method)',
                    type = 'string',
                    values = None,
                ),
                __.FilterCapability(
                    name = 'priority',
                    description = 'Documentation priority level',
                    type = 'string',
                    values = [ '0', '1', '-1' ],
                ),
            ],
            results_limit_max = 100,
            response_time_typical = 'fast',
            notes = 'Works with Sphinx-generated documentation sites',
        )

    async def detect( self, source: str ) -> __.Detection:
        ''' Detects if can process documentation from source. '''
        try: base_url = _urls.normalize_base_url( source )
        except Exception:
            return _detection.SphinxDetection(
                processor = self, confidence = 0.0, source = source )
        has_objects_inv = await _detection.check_objects_inv( base_url )
        if not has_objects_inv:
            return _detection.SphinxDetection(
                processor = self, confidence = 0.0, source = source )
        has_searchindex = await _detection.check_searchindex( base_url )
        confidence = 0.95 if has_searchindex else 0.7
        theme = None
        if has_searchindex:
            try: theme_metadata = await _detection.detect_theme( base_url )
            except Exception as exc:
                _scribe.debug( f"Theme detection failed for {source}: {exc}" )
            else: theme = theme_metadata.get( 'theme' )
        return _detection.SphinxDetection(
            processor = self,
            confidence = confidence,
            source = source,
            has_objects_inv = has_objects_inv,
            has_searchindex = has_searchindex,
            normalized_source = base_url.geturl( ),
            theme = theme )

    async def extract_inventory(
        self,
        source: str, /, *,
        extra_filters: __.typx.Optional[ dict[ str, __.typx.Any ] ] = None,
        details: __.InventoryQueryDetails = (
            __.InventoryQueryDetails.Documentation ),
    ) -> dict[ str, __.typx.Any ]:
        ''' Extracts inventory from Sphinx documentation source. '''
        # TODO: Use details parameter to conditionally extract different levels
        # of information (Name, Signature, Summary, Documentation)
        filters = extra_filters or { }
        domain = filters.get( 'domain', '' ) or __.absent
        role = filters.get( 'role', '' ) or __.absent
        priority = filters.get( 'priority', '' ) or __.absent
        base_url = _urls.normalize_base_url( source )
        inventory = _inventory.extract_inventory( base_url )
        filtered_objects, object_count = _inventory.filter_inventory_basic(
            inventory, domain = domain, role = role, priority = priority )
        result: dict[ str, __.typx.Any ] = {
            'project': inventory.project,
            'version': inventory.version,
            'objects': filtered_objects,
            'object_count': object_count,
        }
        filters_metadata: dict[ str, __.typx.Any ] = { }
        if not __.is_absent( domain ): filters_metadata[ 'domain' ] = domain
        if not __.is_absent( role ): filters_metadata[ 'role' ] = role
        if not __.is_absent( priority ):
            filters_metadata[ 'priority' ] = priority
        if filters_metadata: result[ 'filters' ] = filters_metadata
        return result


    async def extract_documentation(
        self,
        source: str,
        object_name: str, /, *,
        include_sections: __.Absential[ list[ str ] ] = __.absent,
        output_format: str = 'markdown'
    ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        ''' Extracts documentation for specific object from Sphinx source. '''
        base_url = _urls.normalize_base_url( source )
        inventory = _inventory.extract_inventory( base_url )
        found_object = None
        for objct in inventory.objects:
            if objct.name == object_name:
                found_object = objct
                break
        if not found_object:
            return {
                'error': f"Object '{object_name}' not found in inventory" }
        doc_url = _urls.derive_documentation_url(
            base_url, found_object.uri, object_name )
        html_content = await __.retrieve_url_as_text( doc_url )
        anchor = doc_url.fragment or object_name
        parsed_content = _extraction.parse_documentation_html(
            html_content, anchor )
        if 'error' in parsed_content: return parsed_content
        result = {
            'object_name': object_name,
            'url': doc_url.geturl( ),
            'signature': parsed_content[ 'signature' ],
            'description': parsed_content[ 'description' ],
        }
        if output_format == 'markdown':
            result[ 'description' ] = _conversion.html_to_markdown(
                result[ 'description' ] )
        return result

    async def query_documentation(  # noqa: PLR0913
        self,
        source: str, query: str, /, *,
        search_behaviors: __.SearchBehaviors = _search_behaviors_default,
        filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
        include_snippets: bool = True,
        results_max: int = 10,
    ) -> list[ __.cabc.Mapping[ str, __.typx.Any ] ]:
        ''' Queries documentation content from Sphinx source. '''
        base_url = _urls.normalize_base_url( source )
        
        # 1. Extract inventory with processor-specific filtering
        # Use filters dict directly - remove empty values
        processor_filters = {
            k: v for k, v in filters.items( ) if v }
        
        inventory_result = await self.extract_inventory(
            source, extra_filters = processor_filters,
            details = __.InventoryQueryDetails.Name )
        
        # 2. Apply universal search matching
        from ...search import SearchEngine as _SearchEngine
        search_engine = _SearchEngine( )
        all_objects: list[ dict[ str, __.typx.Any ] ] = [ ]
        for domain_objects in inventory_result[ 'objects' ].values( ):
            all_objects.extend( domain_objects )
        
        search_results = search_engine.filter_by_name(
            all_objects, query,
            match_mode = search_behaviors.match_mode,
            fuzzy_threshold = search_behaviors.fuzzy_threshold )
        
        # 3. Get candidates from search results
        candidates = [ result.object for result in search_results ]
        if not candidates: return [ ]
        query_lower = query.lower( )
        # Pre-filter candidates by name relevance before HTTP requests
        name_scored_candidates = _prescore_candidates(
            candidates, query_lower )
        name_scored_candidates.sort( key = lambda x: x[ 0 ], reverse = True )
        fetch_limit = min( len( name_scored_candidates ), results_max * 3 )
        top_candidates = [
            candidate for _, candidate in
            name_scored_candidates[ : fetch_limit ] ]
        tasks = [
            _process_candidate(
                base_url, candidate, query_lower, query, include_snippets )
            for candidate in top_candidates ]
        candidate_results = await __.asyncf.gather_async(
            *tasks, return_exceptions = True )
        # Filter successful results and sort by relevance
        results: list[ __.cabc.Mapping[ str, __.typx.Any ] ] = [
            result.value for result in candidate_results
            if __.generics.is_value( result ) and result.value is not None ]
        results.sort(
            key = lambda x: x[ 'relevance_score' ], reverse = True )
        return results[ : results_max ]


def _prescore_candidates(
    candidates: __.cabc.Sequence[ dict[ str, __.typx.Any ] ],
    query_lower: str
) -> list[ tuple[ float, dict[ str, __.typx.Any ] ] ]:
    ''' Pre-scores candidates by name relevance to avoid HTTP requests. '''
    name_scored_candidates: list[ tuple[
        float, dict[ str, __.typx.Any ]
    ] ] = [ ]
    for candidate in candidates:
        name_score = 0.0
        if query_lower in candidate[ 'name' ].lower( ):
            name_score += 10.0
        if candidate[ 'priority' ] == '1':
            name_score += 2.0
        elif candidate[ 'priority' ] == '0':
            name_score += 1.0
        if name_score > 0:
            name_scored_candidates.append( ( name_score, candidate ) )
    return name_scored_candidates


async def _process_candidate(
    base_url: __.typx.Any, candidate: __.cabc.Mapping[ str, __.typx.Any ],
    query_lower: str, query: str, include_snippets: bool
) -> __.cabc.Mapping[ str, __.typx.Any ] | None:
    ''' Processes a single candidate with HTTP request and scoring. '''
    doc_url = _urls.derive_documentation_url(
        base_url, candidate[ 'uri' ], candidate[ 'name' ] )
    try: html_content = await __.retrieve_url_as_text( doc_url )
    except Exception as exc:
        _scribe.debug( "Failed to retrieve %s: %s", doc_url, exc )
        return None
    anchor = doc_url.fragment or str( candidate[ 'name' ] )
    try:
        parsed_content = _extraction.parse_documentation_html(
            html_content, anchor )
    except Exception: return None
    if 'error' in parsed_content: return None
    description = _conversion.html_to_markdown(
        parsed_content[ 'description' ] )
    doc_result = {
        'signature': parsed_content[ 'signature' ],
        'description': description,
    }
    score, match_reasons = _extraction.calculate_relevance_score(
        query_lower, candidate, doc_result )
    if score <= 0: return None
    content_snippet = ''
    if include_snippets:
        content_snippet = _extraction.extract_content_snippet(
            query_lower, query, description )
    return {
        'object_name': candidate[ 'name' ],
        'object_type': candidate[ 'role' ],
        'domain': candidate[ 'domain' ],
        'priority': candidate[ 'priority' ],
        'url': doc_url.geturl( ),
        'signature': parsed_content[ 'signature' ],
        'description': description,
        'content_snippet': content_snippet,
        'relevance_score': score,
        'match_reasons': match_reasons,
    }
