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

from urllib.parse import ParseResult as _Url

import httpx as _httpx
import sphobjinv as _sphobjinv

from bs4 import BeautifulSoup as _BeautifulSoup

from . import __


_scribe = __.acquire_scribe( __name__ )


class SphinxProcessor( __.Processor ):
    ''' Processor for Sphinx documentation sources. '''

    name: str = 'sphinx'

    async def detect( self, source: str ) -> __.Detection:
        ''' Detects if can process documentation from source. '''
        try: base_url = _normalize_base_url( source )
        except Exception:
            return SphinxDetection(
                processor = self, confidence = 0.0, source = source )
        has_objects_inv = await _check_objects_inv( base_url )
        if not has_objects_inv:
            return SphinxDetection(
                processor = self, confidence = 0.0, source = source )
        has_searchindex = await _check_searchindex( base_url )
        confidence = 0.95 if has_searchindex else 0.7
        theme = None
        if has_searchindex:
            try: theme_metadata = await _detect_theme( base_url )
            except Exception as exc:
                _scribe.debug( f"Theme detection failed for {source}: {exc}" )
            else: theme = theme_metadata.get( 'theme' )
        return SphinxDetection(
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


class SphinxDetection( __.Detection ):
    ''' Detection result for Sphinx documentation sources. '''

    source: str
    has_objects_inv: bool = False
    has_searchindex: bool = False
    normalized_source: str = ''
    theme: __.typx.Optional[ str ] = None

    @classmethod
    async def from_source(
        cls, processor: __.Processor, source: str
    ) -> __.typx.Self:
        ''' Constructs detection from source location. '''
        if not isinstance( processor, SphinxProcessor ):
            raise __.ProcessorTypeError(
                "SphinxProcessor", type( processor ) )
        detection = await processor.detect( source )
        return __.typx.cast( __.typx.Self, detection )


def register( arguments: __.cabc.Mapping[ str, __.typx.Any ] ) -> None:
    ''' Registers configured Sphinx processor instance. '''
    processor = SphinxProcessor( )
    __.processors[ processor.name ] = processor


def _calculate_relevance_score(
    query_lower: str, candidate: __.cabc.Mapping[ str, __.typx.Any ],
    doc_result: __.cabc.Mapping[ str, __.typx.Any ]
) -> tuple[ float, list[ str ] ]:
    ''' Calculates relevance score and match reasons for doc result. '''
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


async def _check_objects_inv( source: _Url ) -> bool:
    ''' Checks if objects.inv exists at the source. '''
    inventory_url = _derive_inventory_url( source )
    return await _probe_url( inventory_url )


async def _check_searchindex( source: _Url ) -> bool:
    ''' Checks if searchindex.js exists (indicates full Sphinx site). '''
    searchindex_url = _derive_searchindex_url( source )
    return await _probe_url( searchindex_url )


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


def _derive_documentation_url(
    base_url: _Url, object_uri: str, object_name: str
) -> _Url:
    ''' Derives documentation URL from base URL ParseResult and object URI. '''
    uri_with_name = object_uri.replace( '$', object_name )
    new_path = f"{base_url.path}/{uri_with_name}"
    return base_url._replace( path = new_path )


def _derive_html_url( base_url: _Url ) -> _Url:
    ''' Derives index.html URL from base URL ParseResult. '''
    new_path = f"{base_url.path}/index.html"
    return base_url._replace( path = new_path )


def _derive_inventory_url( base_url: _Url ) -> _Url:
    ''' Derives objects.inv URL from base URL ParseResult. '''
    new_path = f"{base_url.path}/objects.inv"
    return base_url._replace( path = new_path )


def _derive_searchindex_url( base_url: _Url ) -> _Url:
    ''' Derives searchindex.js URL from base URL ParseResult. '''
    new_path = f"{base_url.path}/searchindex.js"
    return base_url._replace( path = new_path )


async def _detect_theme( source: _Url ) -> dict[ str, __.typx.Any ]:
    ''' Detects Sphinx theme and other metadata. '''
    theme_metadata: dict[ str, __.typx.Any ] = { }
    html_url = _derive_html_url( source )
    try: html_content = await _retrieve_url( html_url, timeout = 10.0 )
    except __.DocumentationInaccessibility: pass
    else:
        html_content_lower = html_content.lower( )
        if 'furo' in html_content_lower:
            theme_metadata[ 'theme' ] = 'furo'
        elif 'alabaster' in html_content_lower:
            theme_metadata[ 'theme' ] = 'alabaster'
        elif 'sphinx_rtd_theme' in html_content_lower:
            theme_metadata[ 'theme' ] = 'sphinx_rtd_theme'
        # If no theme detected, don't set theme key (returns None)
    return theme_metadata


def _extract_content_snippet(
    query_lower: str, query: str, description: str
) -> str:
    ''' Extracts content snippet around query match in description. '''
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


def _extract_inventory( base_url: _Url ) -> _sphobjinv.Inventory:
    ''' Extracts and parses Sphinx inventory from URL or file path. '''
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


def _filter_exact_and_regex_matching( # noqa: PLR0913
    inventory: _sphobjinv.Inventory,
    domain: __.Absential[ str ],
    role: __.Absential[ str ],
    priority: __.Absential[ str ],
    term: str,
    match_mode: __.MatchMode,
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
    match_mode: __.MatchMode = __.MatchMode.Exact,
    fuzzy_threshold: int = 50,
) -> tuple[ dict[ str, __.typx.Any ], int ]:
    ''' Filters inventory objects by domain, role, term, match mode. '''
    term_ = '' if __.is_absent( term ) else term
    if term_ and match_mode == __.MatchMode.Fuzzy:
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


def _normalize_base_url( source: str ) -> __.typx.Annotated[
    _Url,
    __.ddoc.Doc(
        ''' Normalized base URL without trailing slash.

            Extracts clean base documentation URL from any source.
            Handles URLs, file paths, and directories consistently.
        ''' )
]:
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
        case _: raise __.InventoryUrlInvalidity( source )
    path = url.path.rstrip( '/' )
    return _urlparse.ParseResult(
        scheme = url.scheme, netloc = url.netloc, path = path,
        params = '', query = '', fragment = '' )


def _parse_documentation_html(
    html_content: str, element_id: str
) -> __.cabc.Mapping[ str, str ]:
    ''' Parses HTML content to extract documentation sections. '''
    try: soup = _BeautifulSoup( html_content, 'lxml' )
    except Exception as exc:
        raise __.DocumentationParseFailure(
            element_id, exc ) from exc
    main_content = soup.find( 'article', { 'role': 'main' } )
    if not main_content:
        raise __.DocumentationContentAbsence( element_id )
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


async def _probe_url( url: _Url, *, timeout: float = 10.0 ) -> bool:
    ''' Checks if URL exists using HEAD request or file existence check. '''
    match url.scheme:
        case 'file' | '':
            file_path = __.Path( url.path )
            return file_path.exists( )
        case 'http' | 'https':
            try:
                async with _httpx.AsyncClient( timeout = timeout ) as client:
                    response = await client.head( url.geturl( ) )
            except Exception: return False
            else: return response.status_code == _http.HTTPStatus.OK
        case _: return False


async def _retrieve_url( url: _Url, *, timeout: float = 30.0 ) -> str:
    ''' Retrieves content from URL using GET request or file read. '''
    match url.scheme:
        case 'file':
            file_path = __.Path( url.path )
            try: return file_path.read_text( encoding = 'utf-8' )
            except Exception as exc:
                raise __.DocumentationInaccessibility(
                    url.geturl( ), exc ) from exc
        case 'http' | 'https':
            try:
                async with _httpx.AsyncClient( timeout = timeout ) as client:
                    response = await client.get( url.geturl( ) )
                    response.raise_for_status( )
            except Exception as exc:
                raise __.DocumentationInaccessibility(
                    url.geturl( ), exc ) from exc
            else: return response.text
        case _:
            raise __.DocumentationInaccessibility(
                url.geturl( ),
                ValueError( f"Unsupported URL scheme: {url.scheme}" ) )
