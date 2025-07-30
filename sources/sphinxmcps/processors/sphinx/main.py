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

    async def extract_documentation_for_objects(
        self, source: str, objects: list[ dict[ str, __.typx.Any ] ], /, *,
        include_snippets: bool = True,
    ) -> list[ __.cabc.Mapping[ str, __.typx.Any ] ]:
        ''' Extracts documentation content for specified objects. '''
        base_url = _urls.normalize_base_url( source )
        if not objects: return [ ]
        tasks = [
            _extract_object_documentation(
                base_url, obj, include_snippets )
            for obj in objects ]
        candidate_results = await __.asyncf.gather_async(
            *tasks, return_exceptions = True )
        results: list[ __.cabc.Mapping[ str, __.typx.Any ] ] = [
            result.value for result in candidate_results
            if __.generics.is_value( result ) and result.value is not None ]
        return results

    async def extract_filtered_inventory( self, source: str, /, *,
        filters: __.cabc.Mapping[ str, __.typx.Any ] = _filters_default,
        details: __.InventoryQueryDetails = (
            __.InventoryQueryDetails.Documentation ),
    ) -> list[ dict[ str, __.typx.Any ] ]:
        ''' Extracts and filters inventory objects from documentation source.
        '''
        domain = filters.get( 'domain', '' ) or __.absent
        role = filters.get( 'role', '' ) or __.absent
        priority = filters.get( 'priority', '' ) or __.absent
        base_url = _urls.normalize_base_url( source )
        inventory = _inventory.extract_inventory( base_url )
        filtered_objects, object_count = _inventory.filter_inventory_basic(
            inventory, domain = domain, role = role, priority = priority )
        all_objects: list[ dict[ str, __.typx.Any ] ] = [ ]
        for domain_objects in filtered_objects.values( ):
            all_objects.extend( domain_objects )
        for obj in all_objects:
            obj[ '_inventory_project' ] = inventory.project
            obj[ '_inventory_version' ] = inventory.version
        return all_objects


async def _extract_object_documentation(
    base_url: __.typx.Any, obj: dict[ str, __.typx.Any ],
    include_snippets: bool
) -> __.cabc.Mapping[ str, __.typx.Any ] | None:
    ''' Extracts documentation for a single object without query matching. '''
    doc_url = _urls.derive_documentation_url(
        base_url, obj[ 'uri' ], obj[ 'name' ] )
    try: html_content = await __.retrieve_url_as_text( doc_url )
    except Exception as exc:
        _scribe.debug( "Failed to retrieve %s: %s", doc_url, exc )
        return None
    anchor = doc_url.fragment or str( obj[ 'name' ] )
    try:
        parsed_content = _extraction.parse_documentation_html(
            html_content, anchor )
    except Exception: return None
    if 'error' in parsed_content: return None
    description = _conversion.html_to_markdown(
        parsed_content[ 'description' ] )
    snippet_max_length = 200
    if include_snippets:
        content_snippet = (
            description[ : snippet_max_length ] + '...'
            if len( description ) > snippet_max_length
            else description )
    else: content_snippet = ''
    return {
        'object_name': obj[ 'name' ],
        'object_type': obj[ 'role' ],
        'domain': obj[ 'domain' ],
        'priority': obj[ 'priority' ],
        'url': doc_url.geturl( ),
        'signature': parsed_content[ 'signature' ],
        'description': description,
        'content_snippet': content_snippet,
        'relevance_score': 1.0,  # Default score since no query matching
        'match_reasons': [ 'direct extraction' ],
    }
