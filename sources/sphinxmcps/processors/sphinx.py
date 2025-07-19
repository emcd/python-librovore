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


''' Sphinx documentation source detector and processor. '''


import http as _http
import urllib.parse as _urlparse

import httpx as _httpx
import sphobjinv as _sphobjinv

from bs4 import BeautifulSoup as _BeautifulSoup

from . import __
from .. import functions as _functions
from .. import interfaces as _interfaces
from .. import exceptions as _exceptions


class SphinxProcessor( _interfaces.Processor ):
    ''' Processor for Sphinx documentation sources. '''

    name: str = 'sphinx'

    async def detect( self, source: str ) -> _interfaces.Detection:
        ''' Detect if can process documentation from source. '''
        try:
            normalized_source = _functions.normalize_inventory_source( source )
        except Exception:
            return SphinxDetection(
                processor = self, confidence = 0.0, source = source
            )
        has_objects_inv = await _check_objects_inv( normalized_source )
        if not has_objects_inv:
            return SphinxDetection(
                processor = self, confidence = 0.0, source = source )
        has_searchindex = await _check_searchindex( normalized_source )
        confidence = 0.95 if has_searchindex else 0.7
        metadata: dict[ str, __.typx.Any ] = {
            'has_objects_inv': has_objects_inv,
            'has_searchindex': has_searchindex,
            'normalized_source': normalized_source.geturl( ),
        }
        if has_searchindex:
            try:
                theme_metadata = await _detect_theme( normalized_source )
                metadata.update( theme_metadata )
            except Exception as exc:
                metadata[ 'theme_error' ] = str( exc )
        return SphinxDetection(
            processor = self,
            confidence = confidence,
            source = source,
            metadata = metadata )

    def extract_inventory( self, source: str, /, *, # noqa: PLR0913
        domain: __.Absential[ str ] = __.absent,
        role: __.Absential[ str ] = __.absent,
        term: __.Absential[ str ] = __.absent,
        priority: __.Absential[ str ] = __.absent,
        match_mode: _interfaces.MatchMode = _interfaces.MatchMode.Exact,
        fuzzy_threshold: int = 50
    ) -> dict[ str, __.typx.Any ]:
        ''' Extract inventory from Sphinx documentation source. '''
        inventory = _extract_inventory( source )
        filtered_objects, object_count = _filter_inventory(
            inventory, domain = domain, role = role, term = term,
            priority = priority,
            match_mode = match_mode, fuzzy_threshold = fuzzy_threshold
        )
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
        if match_mode != _interfaces.MatchMode.Exact:
            filters[ 'match_mode' ] = match_mode.value
        if match_mode == _interfaces.MatchMode.Fuzzy:
            filters[ 'fuzzy_threshold' ] = fuzzy_threshold
        if filters:
            result[ 'filters' ] = filters
        return result

    def summarize_inventory( self, source: str, /, *, # noqa: PLR0913
        domain: __.Absential[ str ] = __.absent,
        role: __.Absential[ str ] = __.absent,
        term: __.Absential[ str ] = __.absent,
        priority: __.Absential[ str ] = __.absent,
        match_mode: _interfaces.MatchMode = _interfaces.MatchMode.Exact,
        fuzzy_threshold: int = 50
    ) -> str:
        ''' Summarize inventory from Sphinx documentation source. '''
        inventory = _extract_inventory( source )
        filtered_objects, object_count = _filter_inventory(
            inventory, domain = domain, role = role, term = term,
            priority = priority,
            match_mode = match_mode, fuzzy_threshold = fuzzy_threshold
        )
        summary_lines: list[ str ] = [
            f"Project: {inventory.project}",
            f"Version: {inventory.version}",
            f"Objects: {object_count}",
        ]
        filters: list[ str ] = [ ]
        if not __.is_absent( domain ): filters.append( f"domain={domain}" )
        if not __.is_absent( role ): filters.append( f"role={role}" )
        if not __.is_absent( term ): filters.append( f"term={term}" )
        if not __.is_absent( priority ):
            filters.append( f"priority={priority}" )
        if match_mode != _interfaces.MatchMode.Exact:
            filters.append( f"match_mode={match_mode.value}" )
        if match_mode == _interfaces.MatchMode.Fuzzy:
            filters.append( f"fuzzy_threshold={fuzzy_threshold}" )
        if filters:
            summary_lines.append( f"Filters: {', '.join( filters )}" )
        if filtered_objects:
            summary_lines.append( "\nDomain breakdown:" )
            for domain_name, objects in filtered_objects.items( ):
                summary_lines.append(
                    f"  {domain_name}: {len( objects )} objects"
                )
        return "\n".join( summary_lines )

    async def extract_documentation(
        self, source: str, object_name: str, /, *,
        include_sections: __.Absential[ list[ str ] ] = __.absent,
        output_format: str = 'markdown'
    ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        ''' Extract documentation for specific object from Sphinx source. '''
        inventory = _extract_inventory( source )
        found_object = None
        for objct in inventory.objects:
            if objct.name == object_name:
                found_object = objct
                break
        if not found_object:
            return {
                'error': f"Object '{object_name}' not found in inventory"
            }
        base_url = _extract_base_url( source )
        doc_url = _build_documentation_url(
            base_url, found_object.uri, object_name )
        html_content = await _fetch_html_content( doc_url )
        url_parts = _urlparse.urlparse( doc_url )
        anchor = url_parts.fragment or object_name
        parsed_content = _parse_documentation_html( html_content, anchor )
        if 'error' in parsed_content:
            return parsed_content
        result = {
            'object_name': object_name,
            'url': doc_url,
            'signature': parsed_content[ 'signature' ],
            'description': parsed_content[ 'description' ],
        }
        if output_format == 'markdown':
            result[ 'description' ] = _html_to_markdown(
                result[ 'description' ]
            )
        return result

    async def query_documentation( self, source: str, query: str, /, *, # noqa: PLR0913,PLR0915
        domain: __.Absential[ str ] = __.absent,
        role: __.Absential[ str ] = __.absent,
        priority: __.Absential[ str ] = __.absent,
        match_mode: _interfaces.MatchMode = _interfaces.MatchMode.Fuzzy,
        fuzzy_threshold: int = 50,
        max_results: int = 10,
        include_snippets: bool = True
    ) -> list[ __.cabc.Mapping[ str, __.typx.Any ] ]:
        ''' Query documentation content from Sphinx source. '''
        inventory = _extract_inventory( source )
        filtered_objects, _ = _filter_inventory(
            inventory, domain = domain, role = role,
            priority = priority,
            match_mode = match_mode, fuzzy_threshold = fuzzy_threshold )
        candidates: list[ __.cabc.Mapping[ str, __.typx.Any ] ] = [ ]
        for domain_objects in filtered_objects.values( ):
            candidates.extend( domain_objects )
        if not candidates: return [ ]
        base_url = _extract_base_url( source )
        query_lower = query.lower( )
        results: list[ __.cabc.Mapping[ str, __.typx.Any ] ] = [ ]
        for candidate in candidates:
            doc_url = _build_documentation_url(
                base_url, candidate[ 'uri' ], candidate[ 'name' ] )
            try: html_content = await _fetch_html_content( doc_url )
            except Exception: # noqa: S112
                continue
            url_parts = _urlparse.urlparse( doc_url )
            anchor = url_parts.fragment or str( candidate[ 'name' ] )
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
                    'url': doc_url,
                    'signature': parsed_content[ 'signature' ],
                    'description': description,
                    'content_snippet': content_snippet,
                    'relevance_score': score,
                    'match_reasons': match_reasons,
                } )
        results.sort( key = lambda x: x[ 'relevance_score' ], reverse = True )
        return results[ : max_results ]


class SphinxDetection( _interfaces.Detection ):
    ''' Detection result for Sphinx documentation sources. '''

    source: str
    metadata: dict[ str, __.typx.Any ] = __.dcls.field(
        default_factory = dict[ str, __.typx.Any ] )

    @classmethod
    async def from_source(
        cls, processor: _interfaces.Processor, source: str
    ) -> __.typx.Self:
        ''' Constructs detection from source location. '''
        if not isinstance( processor, SphinxProcessor ):
            raise _exceptions.ProcessorTypeError(
                "SphinxProcessor", type( processor ) )
        detection = await processor.detect( source )
        return __.typx.cast( __.typx.Self, detection )

    @property
    def specifics( self ) -> _interfaces.DetectionSpecifics:
        ''' Returns metadata associated with detection as dictionary. '''
        return {
            'source': self.source,
            'processor_name': self.processor.name,
            **self.metadata
        }


def _build_documentation_url(
    base_url: str, object_uri: str, object_name: str
) -> str:
    ''' Constructs documentation URL from base URL and object URI. '''
    uri_with_name = object_uri.replace( '$', object_name )
    return "{base_url}/{object_uri}".format(
        base_url = base_url.rstrip( '/' ), object_uri = uri_with_name )


def _calculate_relevance_score(
    query_lower: str, candidate: __.cabc.Mapping[ str, __.typx.Any ],
    doc_result: __.cabc.Mapping[ str, __.typx.Any ]
) -> tuple[ float, list[ str ] ]:
    ''' Calculate relevance score and match reasons for doc result. '''
    score = 0.0
    match_reasons: list[ str ] = [ ]
    if query_lower in candidate[ 'name' ].lower( ):
        score += 10.0
        match_reasons.append( 'name match' )
    if query_lower in doc_result[ 'signature' ].lower( ):
        score += 5.0
        match_reasons.append( 'signature match' )
    if query_lower in doc_result[ 'description' ].lower( ):
        score += 3.0
        match_reasons.append( 'description match' )
    if candidate[ 'priority' ] == '1':
        score += 2.0
    elif candidate[ 'priority' ] == '0':
        score += 1.0
    return score, match_reasons


def _build_html_url(
    normalized_source: _urlparse.ParseResult
) -> _urlparse.ParseResult:
    # TODO: Just pass in the base path instead of stripping suffixes.
    ''' Build main HTML URL from objects.inv URL. '''
    path = normalized_source.path
    if path.endswith( '/objects.inv' ):
        base_path = path[ :-12 ]
    elif path.endswith( 'objects.inv' ):
        base_path = path[ :-11 ]
    else:
        base_path = path
    normalized_base = base_path.rstrip( '/' ) + '/'
    html_path = normalized_base + 'index.html'
    return normalized_source._replace( path = html_path )


def _build_searchindex_url(
    normalized_source: _urlparse.ParseResult
) -> _urlparse.ParseResult:
    # TODO: Just pass in the base path instead of stripping suffixes.
    ''' Build searchindex.js URL from objects.inv URL. '''
    path = normalized_source.path
    if path.endswith( '/objects.inv' ):
        base_path = path[ :-12 ]
    elif path.endswith( 'objects.inv' ):
        base_path = path[ :-11 ]
    else:
        base_path = path
    normalized_base = base_path.rstrip( '/' ) + '/'
    searchindex_path = normalized_base + 'searchindex.js'
    return normalized_source._replace( path = searchindex_path )


async def _check_objects_inv(
    normalized_source: _urlparse.ParseResult
) -> bool:
    ''' Check if objects.inv exists at the source. '''
    if normalized_source.scheme in ( 'file', '' ):
        try:
            objects_inv_path = __.Path( normalized_source.path )
            return objects_inv_path.exists( )
        except Exception: return False
    try:
        async with _httpx.AsyncClient( timeout = 10.0 ) as client:
            response = await client.head( normalized_source.geturl( ) )
            return response.status_code == _http.HTTPStatus.OK
    except Exception: return False


async def _check_searchindex(
    normalized_source: _urlparse.ParseResult
) -> bool:
    ''' Check if searchindex.js exists (indicates full Sphinx site). '''
    searchindex_url = _build_searchindex_url( normalized_source )
    if searchindex_url.scheme in ( 'file', '' ):
        try:
            searchindex_path = __.Path( searchindex_url.path )
            return searchindex_path.exists( )
        except Exception: return False
    try:
        async with _httpx.AsyncClient( timeout = 10.0 ) as client:
            response = await client.head( searchindex_url.geturl( ) )
            return response.status_code == _http.HTTPStatus.OK
    except Exception: return False


def _collect_matching_objects(
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
        objects[ objct.domain ].append( _format_inventory_object( objct ) )
        selections_total += 1
    return objects, selections_total


def _create_term_matcher(
    term: str,
    match_mode: _interfaces.MatchMode
) -> __.cabc.Callable[ [ __.typx.Any ], bool ]:
    ''' Creates a matcher function for term filtering. '''
    if not term: return lambda obj: True
    if match_mode == _interfaces.MatchMode.Regex:
        try: pattern = __.re.compile( term, __.re.IGNORECASE )
        except __.re.error as exc:
            message = f"Invalid regex pattern: {term}"
            raise _exceptions.InventoryFilterInvalidity( message ) from exc
        return lambda obj: bool( pattern.search( obj.name ) )
    term_lower = term.lower( )
    return lambda obj: term_lower in obj.name.lower( )


async def _detect_theme(
    normalized_source: _urlparse.ParseResult
) -> dict[ str, __.typx.Any ]:
    ''' Detect Sphinx theme and other metadata. '''
    theme_metadata: dict[ str, __.typx.Any ] = { }
    html_url = _build_html_url( normalized_source )
    async with _httpx.AsyncClient( timeout = 10.0 ) as client:
        response = await client.get( html_url.geturl( ) )
        if response.status_code == _http.HTTPStatus.OK:
            html_content = response.text.lower( )
            if 'furo' in html_content:
                theme_metadata[ 'theme' ] = 'furo'
            elif 'alabaster' in html_content:
                theme_metadata[ 'theme' ] = 'alabaster'
            elif 'sphinx_rtd_theme' in html_content:
                theme_metadata[ 'theme' ] = 'sphinx_rtd_theme'
            else:
                theme_metadata[ 'theme' ] = 'unknown'
    return theme_metadata


def _extract_base_url( source: str ) -> str:
    ''' Extracts base documentation URL from inventory source. '''
    url = _functions.normalize_inventory_source( source )
    path = url.path.rstrip( '/objects.inv' )
    if not path.endswith( '/' ): path += '/'
    return _urlparse.urlunparse(
        _urlparse.ParseResult(
            scheme = url.scheme, netloc = url.netloc, path = path,
            params='', query='', fragment='' ) )


def _extract_content_snippet(
    query_lower: str, query: str, description: str
) -> str:
    ''' Extract content snippet around query match in description. '''
    if not description or query_lower not in description.lower( ):
        return ''
    query_pos = description.lower( ).find( query_lower )
    start = max( 0, query_pos - 50 )
    end = min( len( description ), query_pos + len( query ) + 50 )
    content_snippet = description[ start:end ]
    if start > 0:
        content_snippet = '...' + content_snippet
    if end < len( description ):
        content_snippet = content_snippet + '...'
    return content_snippet


def _extract_inventory( source: str ) -> _sphobjinv.Inventory:
    ''' Extracts and parses Sphinx inventory from URL or file path. '''
    url = _functions.normalize_inventory_source( source )
    url_s = _urlparse.urlunparse( url )
    nomargs: __.NominativeArguments = { }
    match url.scheme:
        case 'http' | 'https': nomargs[ 'url' ] = url_s
        case 'file': nomargs[ 'fname_zlib' ] = url.path
        case _:
            raise _exceptions.InventoryUrlNoSupport(
                url, component='scheme', value = url.scheme )
    try:
        return _sphobjinv.Inventory( **nomargs )
    except ( ConnectionError, OSError, TimeoutError ) as exc:
        raise _exceptions.InventoryInaccessibility(
            url_s, cause = exc ) from exc
    except Exception as exc:
        raise _exceptions.InventoryInvalidity(
            url_s, cause = exc ) from exc


def _extract_names_from_suggestions(
    suggestions: list[ str ]
) -> set[ str ]:
    ''' Extracts object names from sphobjinv suggestion format. '''
    fuzzy_names: set[ str ] = set( )
    for suggestion in suggestions:
        if '`' in suggestion:
            name = suggestion.split( '`' )[ 1 ]
            fuzzy_names.add( name )
    return fuzzy_names


async def _fetch_html_content( url: str ) -> str:
    ''' Fetches HTML content from documentation URL or local file. '''
    parsed_url = _urlparse.urlparse( url )
    match parsed_url.scheme:
        case 'file':
            try:
                file_path = __.Path( parsed_url.path )
                return file_path.read_text( encoding = 'utf-8' )
            except Exception as exc:
                raise _exceptions.DocumentationInaccessibility(
                    url, exc ) from exc
        case 'http' | 'https':
            try:
                async with _httpx.AsyncClient( timeout = 30.0 ) as client:
                    response = await client.get( url )
                    response.raise_for_status( )
                    return response.text
            except Exception as exc:
                raise _exceptions.DocumentationInaccessibility(
                    url, exc ) from exc
        case _:
            raise _exceptions.DocumentationInaccessibility(
                url,
                ValueError( f"Unsupported URL scheme: {parsed_url.scheme}" ) )


def _filter_exact_and_regex_matching( # noqa: PLR0913
    inventory: _sphobjinv.Inventory,
    domain: __.Absential[ str ],
    role: __.Absential[ str ],
    priority: __.Absential[ str ],
    term: str,
    match_mode: _interfaces.MatchMode,
) -> tuple[ dict[ str, __.typx.Any ], int ]:
    ''' Filters inventory using exact or regex matching. '''
    term_matcher = _create_term_matcher( term, match_mode )
    return _collect_matching_objects(
        inventory, domain, role, priority, term_matcher )


def _filter_fuzzy_matching( # noqa: PLR0913
    inventory: _sphobjinv.Inventory,
    domain: __.Absential[ str ],
    role: __.Absential[ str ],
    priority: __.Absential[ str ],
    term: str,
    fuzzy_threshold: int,
) -> tuple[ dict[ str, __.typx.Any ], int ]:
    ''' Filters inventory using fuzzy matching via sphobjinv.suggest(). '''
    suggestions = inventory.suggest( term, thresh = fuzzy_threshold )
    fuzzy_names = _extract_names_from_suggestions( suggestions )
    return _collect_matching_objects(
        inventory, domain, role, priority,
        lambda obj: obj.name in fuzzy_names )


def _filter_inventory( # noqa: PLR0913
    inventory: _sphobjinv.Inventory,
    domain: __.Absential[ str ] = __.absent,
    role: __.Absential[ str ] = __.absent,
    term: __.Absential[ str ] = __.absent,
    priority: __.Absential[ str ] = __.absent,
    match_mode: _interfaces.MatchMode = _interfaces.MatchMode.Exact,
    fuzzy_threshold: int = 50,
) -> tuple[ dict[ str, __.typx.Any ], int ]:
    ''' Filters inventory objects by domain, role, term, match mode. '''
    term_ = '' if __.is_absent( term ) else term
    if term_ and match_mode == _interfaces.MatchMode.Fuzzy:
        return _filter_fuzzy_matching(
            inventory, domain, role, priority, term_, fuzzy_threshold )
    return _filter_exact_and_regex_matching(
        inventory, domain, role, priority, term_, match_mode )


def _format_inventory_object(
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


def _html_to_markdown( html_text: str ) -> str:
    ''' Converts HTML text to clean markdown format. '''
    if not html_text.strip( ): return ''
    try: soup = _BeautifulSoup( html_text, 'lxml' )
    except Exception: return html_text
    for code in soup.find_all( 'code' ):
        code.replace_with( f"`{code.get_text( )}`" )
    for pre in soup.find_all( 'pre' ):
        pre.replace_with( f"```\n{pre.get_text( )}\n```" )
    for strong in soup.find_all( 'strong' ):
        strong.replace_with( f"**{strong.get_text( )}**" )
    for em in soup.find_all( 'em' ):
        em.replace_with( f"*{em.get_text( )}*" )
    for link in soup.find_all( 'a' ):
        href = link.get( 'href', '' )
        text = link.get_text( )
        if href: link.replace_with( f"[{text}]({href})" )
        else: link.replace_with( text )
    text = soup.get_text( )
    text = __.re.sub( r'\n\s*\n', '\n\n', text )
    text = __.re.sub( r'^\s+|\s+$', '', text, flags = __.re.MULTILINE )
    return text.strip( )


def _parse_documentation_html(
    html_content: str, element_id: str
) -> __.cabc.Mapping[ str, str ]:
    ''' Parses HTML content to extract documentation sections. '''
    try: soup = _BeautifulSoup( html_content, 'lxml' )
    except Exception as exc:
        raise _exceptions.DocumentationParseFailure(
            element_id, exc ) from exc
    main_content = soup.find( 'article', { 'role': 'main' } )
    if not main_content:
        raise _exceptions.DocumentationContentAbsence( element_id )
    object_element = main_content.find( id = element_id )
    if not object_element:
        return { 'error': f"Object '{element_id}' not found in page" }
    if object_element.name == 'dt':
        signature = object_element.get_text( strip = True )
        description_element = object_element.find_next_sibling( 'dd' )
        if description_element:
            for header_link in description_element.find_all(
                'a', class_ = 'headerlink'
            ): header_link.decompose( )
            description = description_element.get_text( strip = True )
        else: description = ''
    elif object_element.name == 'section':
        header = object_element.find( [ 'h1', 'h2', 'h3', 'h4', 'h5', 'h6' ] )
        signature = header.get_text( strip = True ) if header else ''
        description_element = object_element.find( 'p' )
        if description_element:
            description = description_element.get_text( strip = True )
        else: description = ''
    else:
        signature = object_element.get_text( strip = True )
        description = ''
    return {
        'signature': signature,
        'description': description,
        'object_name': element_id,
    }


_sphinx_processor = SphinxProcessor( )


def register(
    arguments: __.cabc.Mapping[ str, __.typx.Any ] | None = None
) -> None:
    ''' Register the Sphinx processor with the processors registry. '''
    from .. import xtnsapi as _xtnsapi
    
    # TODO: Apply configuration arguments to processor instance
    # For now, we ignore arguments but accept them for future use
    if arguments:
        # Future: Configure processor with arguments like timeouts, cache
        # settings, etc.
        pass
    
    _xtnsapi.processors[ _sphinx_processor.name ] = _sphinx_processor


def get_processor( ) -> SphinxProcessor:
    ''' Get the Sphinx processor instance. '''
    return _sphinx_processor
