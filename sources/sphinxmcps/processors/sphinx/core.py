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


''' Core Sphinx processor implementation. '''


from . import __
from .detection import SphinxDetection as _SphinxDetection
from .detection import check_objects_inv as _check_objects_inv
from .detection import check_searchindex as _check_searchindex
from .detection import detect_theme as _detect_theme
from .urls import normalize_base_url as _normalize_base_url
from .urls import derive_documentation_url as _derive_documentation_url
from .inventory import extract_inventory as _extract_inventory
from .inventory import filter_inventory as _filter_inventory
from .extraction import retrieve_url as _retrieve_url
from .extraction import parse_documentation_html as _parse_documentation_html
from .extraction import calculate_relevance_score as _calculate_relevance_score
from .extraction import extract_content_snippet as _extract_content_snippet
from .conversion import html_to_markdown as _html_to_markdown


_scribe = __.acquire_scribe( __name__ )


class SphinxProcessor( __.Processor ):
    ''' Processor for Sphinx documentation sources. '''

    name: str = 'sphinx'

    async def detect( self, source: str ) -> __.Detection:
        ''' Detects if can process documentation from source. '''
        try: base_url = _normalize_base_url( source )
        except Exception:
            return _SphinxDetection(
                processor = self, confidence = 0.0, source = source )
        has_objects_inv = await _check_objects_inv( base_url )
        if not has_objects_inv:
            return _SphinxDetection(
                processor = self, confidence = 0.0, source = source )
        has_searchindex = await _check_searchindex( base_url )
        confidence = 0.95 if has_searchindex else 0.7
        theme = None
        if has_searchindex:
            try: theme_metadata = await _detect_theme( base_url )
            except Exception as exc:
                _scribe.debug( f"Theme detection failed for {source}: {exc}" )
            else: theme = theme_metadata.get( 'theme' )
        return _SphinxDetection(
            processor = self,
            confidence = confidence,
            source = source,
            has_objects_inv = has_objects_inv,
            has_searchindex = has_searchindex,
            normalized_source = base_url.geturl( ),
            theme = theme )

    async def extract_inventory( # noqa: PLR0913
        self,
        source: str, /, *,
        domain: __.Absential[ str ] = __.absent,
        role: __.Absential[ str ] = __.absent,
        term: __.Absential[ str ] = __.absent,
        priority: __.Absential[ str ] = __.absent,
        match_mode: __.MatchMode = __.MatchMode.Exact,
        fuzzy_threshold: int = 50,
    ) -> dict[ str, __.typx.Any ]:
        ''' Extracts inventory from Sphinx documentation source. '''
        base_url = _normalize_base_url( source )
        inventory = _extract_inventory( base_url )
        filtered_objects, object_count = _filter_inventory(
            inventory, domain = domain, role = role, term = term,
            priority = priority,
            match_mode = match_mode, fuzzy_threshold = fuzzy_threshold )
        result: dict[ str, __.typx.Any ] = {
            'project': inventory.project,
            'version': inventory.version,
            'objects': filtered_objects,
            'object_count': object_count,
        }
        filters: dict[ str, __.typx.Any ] = { }
        if not __.is_absent( domain ): filters[ 'domain' ] = domain
        if not __.is_absent( role ): filters[ 'role' ] = role
        if not __.is_absent( term ): filters[ 'term' ] = term
        if not __.is_absent( priority ): filters[ 'priority' ] = priority
        if match_mode != __.MatchMode.Exact:
            filters[ 'match_mode' ] = match_mode.value
        if match_mode == __.MatchMode.Fuzzy:
            filters[ 'fuzzy_threshold' ] = fuzzy_threshold
        if filters:
            result[ 'filters' ] = filters
        return result


    async def extract_documentation(
        self,
        source: str,
        object_name: str, /, *,
        include_sections: __.Absential[ list[ str ] ] = __.absent,
        output_format: str = 'markdown'
    ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        ''' Extracts documentation for specific object from Sphinx source. '''
        base_url = _normalize_base_url( source )
        inventory = _extract_inventory( base_url )
        found_object = None
        for objct in inventory.objects:
            if objct.name == object_name:
                found_object = objct
                break
        if not found_object:
            return {
                'error': f"Object '{object_name}' not found in inventory"
            }
        doc_url = _derive_documentation_url(
            base_url, found_object.uri, object_name )
        html_content = await _retrieve_url( doc_url )
        anchor = doc_url.fragment or object_name
        parsed_content = _parse_documentation_html( html_content, anchor )
        if 'error' in parsed_content: return parsed_content
        result = {
            'object_name': object_name,
            'url': doc_url.geturl( ),
            'signature': parsed_content[ 'signature' ],
            'description': parsed_content[ 'description' ],
        }
        if output_format == 'markdown':
            result[ 'description' ] = _html_to_markdown(
                result[ 'description' ] )
        return result

    async def query_documentation( # noqa: PLR0913,PLR0915
        self,
        source: str, query: str, /, *,
        domain: __.Absential[ str ] = __.absent,
        role: __.Absential[ str ] = __.absent,
        priority: __.Absential[ str ] = __.absent,
        match_mode: __.MatchMode = __.MatchMode.Fuzzy,
        fuzzy_threshold: int = 50,
        max_results: int = 10,
        include_snippets: bool = True
    ) -> list[ __.cabc.Mapping[ str, __.typx.Any ] ]:
        ''' Queries documentation content from Sphinx source. '''
        base_url = _normalize_base_url( source )
        inventory = _extract_inventory( base_url )
        filtered_objects, _ = _filter_inventory(
            inventory, domain = domain, role = role,
            priority = priority,
            match_mode = match_mode, fuzzy_threshold = fuzzy_threshold )
        candidates: list[ __.cabc.Mapping[ str, __.typx.Any ] ] = [ ]
        for domain_objects in filtered_objects.values( ):
            candidates.extend( domain_objects )
        if not candidates: return [ ]
        base_url = _normalize_base_url( source )
        query_lower = query.lower( )
        results: list[ __.cabc.Mapping[ str, __.typx.Any ] ] = [ ]
        for candidate in candidates:
            doc_url = _derive_documentation_url(
                base_url, candidate[ 'uri' ], candidate[ 'name' ] )
            try: html_content = await _retrieve_url( doc_url )
            except Exception: # noqa: S112
                continue
            anchor = doc_url.fragment or str( candidate[ 'name' ] )
            try:
                parsed_content = _parse_documentation_html(
                    html_content, anchor )
            except Exception: # noqa: S112
                continue
            if 'error' in parsed_content: continue
            description = _html_to_markdown( parsed_content[ 'description' ] )
            doc_result = {
                'signature': parsed_content[ 'signature' ],
                'description': description,
            }
            score, match_reasons = _calculate_relevance_score(
                query_lower, candidate, doc_result )
            if score > 0:
                content_snippet = ''
                if include_snippets:
                    content_snippet = _extract_content_snippet(
                        query_lower, query, description )
                results.append( {
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
                } )
        results.sort( key = lambda x: x[ 'relevance_score' ], reverse = True )
        return results[ : max_results ]