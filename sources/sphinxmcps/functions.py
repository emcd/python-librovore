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


''' Core business logic shared between CLI and MCP server. '''


import urllib.parse as _urlparse

from bs4 import BeautifulSoup as _BeautifulSoup
import httpx as _httpx
import sphobjinv as _sphobjinv

from . import __
from . import exceptions as _exceptions
from . import interfaces as _interfaces


DocumentationResult: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]
DomainFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ str ],
    __.ddoc.Doc( ''' Filter objects by domain (e.g., 'py', 'std'). ''' )
]
FuzzyThreshold: __.typx.TypeAlias = __.typx.Annotated[
    int,
    __.ddoc.Doc( ''' Fuzzy matching threshold (0-100, higher = stricter). ''' )
]
RoleFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ str ],
    __.ddoc.Doc( ''' Filter objects by role (e.g., 'function'). ''' )
]
TermFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ str ],
    __.ddoc.Doc( ''' Filter objects by name containing this text. ''' )
]
MatchModeArgument: __.typx.TypeAlias = __.typx.Annotated[
    _interfaces.MatchMode,
    __.ddoc.Doc( ''' Term matching mode: exact, regex, or fuzzy. ''' )
]
PriorityFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ str ],
    __.ddoc.Doc( ''' Filter objects by priority level (e.g., '1', '0'). ''' )
]
RegexFlag: __.typx.TypeAlias = __.typx.Annotated[
    bool, __.ddoc.Doc( ''' Use regex pattern matching for term filter. ''' )
]
SearchResult: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]
SectionFilter: __.typx.TypeAlias = __.typx.Annotated[
    __.Absential[ list[ str ] ],
    __.ddoc.Doc( ''' Sections to include (signature, description). ''' )
]
SourceArgument: __.typx.TypeAlias = __.typx.Annotated[
    str, __.ddoc.Doc( ''' URL or file path to Sphinx documentation. ''' )
]


async def extract_documentation(
    source: SourceArgument,
    object_name: str, /, *,
    include_sections: SectionFilter = __.absent,
) -> DocumentationResult:
    ''' Extracts documentation for a specific object from Sphinx docs. '''
    inventory = _extract_inventory( source )
    found_object = None
    for objct in inventory.objects:
        if objct.name == object_name:
            found_object = objct
            break
    if not found_object:
        return { 'error': f"Object '{object_name}' not found in inventory" }
    base_url = _extract_base_url( source )
    doc_url = _build_documentation_url(
        base_url, found_object.uri, object_name )
    html_content = await _fetch_html_content( doc_url )
    # Extract the anchor from the URL to find the element
    url_parts = _urlparse.urlparse( doc_url )
    anchor = url_parts.fragment or object_name
    parsed_content = _parse_documentation_html( html_content, anchor )
    if 'error' in parsed_content: return parsed_content
    result = {
        'object_name': object_name,
        'url': doc_url,
        'signature': parsed_content[ 'signature' ],
        'description': parsed_content[ 'description' ],
    }
    result[ 'description' ] = _html_to_markdown( result[ 'description' ] )
    return result


def _calculate_relevance_score(
    query_lower: str, candidate: __.cabc.Mapping[ str, __.typx.Any ],
    doc_result: __.cabc.Mapping[ str, __.typx.Any ]
) -> __.typx.Annotated[
    tuple[ float, list[ str ] ],
    __.ddoc.Doc( ''' Relevance score and match reasons for a result. ''' )
]:
    ''' Calculate relevance score and match reasons for doc result. '''
    score = 0.0
    match_reasons: list[ str ] = []

    # Name matching (highest weight)
    if query_lower in candidate['name'].lower( ):
        score += 10.0
        match_reasons.append('name match')

    # Signature matching
    if query_lower in doc_result['signature'].lower( ):
        score += 5.0
        match_reasons.append('signature match')

    # Description matching
    if query_lower in doc_result['description'].lower( ):
        score += 3.0
        match_reasons.append( 'description match' )

    # Priority boost
    if candidate['priority'] == '1':
        score += 2.0
    elif candidate['priority'] == '0':
        score += 1.0

    return score, match_reasons


def _extract_content_snippet(
    query_lower: str, query: str, description: str
) -> __.typx.Annotated[
    str, __.ddoc.Doc( ''' Content snippet around the query match. ''' )
]:
    ''' Extract content snippet around query match in description. '''
    if not description or query_lower not in description.lower( ):
        return ''

    # Find query in description and extract surrounding context
    query_pos = description.lower( ).find(query_lower)
    start = max(0, query_pos - 50)
    end = min(len(description), query_pos + len(query) + 50)
    content_snippet = description[start:end]

    if start > 0:
        content_snippet = '...' + content_snippet
    if end < len(description):
        content_snippet = content_snippet + '...'

    return content_snippet


async def query_documentation(  # noqa: PLR0913
    source: SourceArgument,
    query: str, /, *,
    domain: DomainFilter = __.absent,
    role: RoleFilter = __.absent,
    priority: PriorityFilter = __.absent,
    match_mode: _interfaces.MatchMode = _interfaces.MatchMode.Fuzzy,
    fuzzy_threshold: int = 50,
    max_results: int = 10,
    include_snippets: bool = True
) -> __.typx.Annotated[
    list[ __.cabc.Mapping[ str, __.typx.Any ] ],
    __.ddoc.Doc( ''' List of query results with relevance ranking. ''' )
]:
    ''' Queries documentation content with relevance ranking. '''
    # Step 1: Use inventory filtering to find candidate objects
    inventory_results = extract_inventory(
        source,
        domain = domain,
        role = role,
        term = query,
        priority = priority,
        match_mode = match_mode,
        fuzzy_threshold = fuzzy_threshold )
    if 'objects' not in inventory_results: return [ ]
    # Step 2: Extract documentation for each candidate object
    candidates = [
        obj for domain_objects in inventory_results['objects'].values( )
        for obj in domain_objects ]
    # Step 3: Fetch documentation content and calculate relevance
    results: list[ __.cabc.Mapping[ str, __.typx.Any ] ] = [ ]
    query_lower = query.lower( )
    for candidate in candidates:
        try:
            doc_result = await extract_documentation(
                source, candidate['name'] )
            if 'error' in doc_result:
                continue
            # Calculate relevance score
            score, match_reasons = _calculate_relevance_score(
                query_lower, candidate, doc_result )
            # Extract content snippet if requested
            content_snippet = ''
            if include_snippets:
                content_snippet = _extract_content_snippet(
                    query_lower, query, doc_result['description'] )
            results.append({
                'object_name': candidate['name'],
                'object_type': candidate['role'],
                'domain': candidate.get('domain', ''),
                'priority': candidate['priority'],
                'url': doc_result['url'],
                'signature': doc_result['signature'],
                'description': doc_result['description'],
                'content_snippet': content_snippet,
                'relevance_score': score,
                'match_reasons': match_reasons
            })
        except Exception:  # noqa: S112
            # Skip objects that can't be processed
            continue
    # Step 4: Sort by relevance and return top results
    results.sort( key = lambda x: x[ 'relevance_score' ], reverse = True )
    return results[ : max_results ]


def extract_inventory( # noqa: PLR0913
    source: SourceArgument, /, *,
    domain: DomainFilter = __.absent,
    role: RoleFilter = __.absent,
    term: TermFilter = __.absent,
    priority: PriorityFilter = __.absent,
    match_mode: MatchModeArgument = _interfaces.MatchMode.Exact,
    fuzzy_threshold: FuzzyThreshold = 50,
) -> __.typx.Annotated[
    dict[ str, __.typx.Any ],
    __.ddoc.Doc(
        ''' Dictionary containing inventory metadata and filtered objects.

            Contains project info, version, source, object counts, domain
            summary, and the actual objects grouped by domain.
        ''' )
]:
    ''' Extracts Sphinx inventory from source with optional filtering. '''
    inventory = _extract_inventory( source )
    objects, selections_total = (
        _filter_inventory(
            inventory,
            domain = domain, role = role, term = term, priority = priority,
            match_mode = match_mode, fuzzy_threshold = fuzzy_threshold )
    )
    domains_summary: dict[ str, int ] = {
        domain_name: len( objs )
        for domain_name, objs in objects.items( ) }
    result: dict[ str, __.typx.Any ] = {
        'project': inventory.project,
        'version': inventory.version,
        'source': source,
        'object_count': selections_total,
        'domains': domains_summary,
        'objects': objects,
    }
    if ( any( ( domain, role, term, priority ) )
         or match_mode != _interfaces.MatchMode.Exact ):
        result[ 'filters' ] = { }
        if not __.is_absent( domain ):
            result[ 'filters' ][ 'domain' ] = domain
        if not __.is_absent( role ):
            result[ 'filters' ][ 'role' ] = role
        if not __.is_absent( term ):
            result[ 'filters' ][ 'term' ] = term
        if not __.is_absent( priority ):
            result[ 'filters' ][ 'priority' ] = priority
        if match_mode != _interfaces.MatchMode.Exact:
            result[ 'filters' ][ 'match_mode' ] = match_mode.value
            if match_mode == _interfaces.MatchMode.Fuzzy:
                result[ 'filters' ][ 'fuzzy_threshold' ] = fuzzy_threshold
    return result


def summarize_inventory( # noqa: PLR0913
    source: SourceArgument, /, *,
    domain: DomainFilter = __.absent,
    role: RoleFilter = __.absent,
    term: TermFilter = __.absent,
    priority: PriorityFilter = __.absent,
    match_mode: MatchModeArgument = _interfaces.MatchMode.Exact,
    fuzzy_threshold: FuzzyThreshold = 50,
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( ''' Human-readable summary of inventory contents. ''' )
]:
    ''' Provides human-readable summary of a Sphinx inventory. '''
    data = extract_inventory(
        source, domain = domain, role = role, term = term, priority = priority,
        match_mode = match_mode, fuzzy_threshold = fuzzy_threshold )
    lines = [
        "Sphinx Inventory: {project} v{version}".format(
            project = data[ 'project' ], version = data[ 'version' ]
        ),
        "Source: {source}".format( source = data[ 'source' ] ),
        "Total Objects: {count}".format( count = data[ 'object_count' ] ),
    ]
    filters = data.get( 'filters' )
    # Show filter information if present
    if filters and any( filters.values( ) ):
        filter_parts: list[ str ] = [ ]
        for filter_name, filter_value in filters.items( ):
            if filter_value:
                filter_parts.append( "{name}={value}".format(
                    name = filter_name, value = filter_value ) )
        if filter_parts:
            lines.append( "Filters: {parts}".format(
                parts = ', '.join( filter_parts ) ) )
    lines.extend( [ "", "Domains:" ] )
    for domain_, count in sorted( data[ 'domains' ].items( ) ):
        lines.append( "  {domain}: {count} objects".format(
            domain = domain_, count = count ) )
    # Show sample objects from largest domain
    if data[ 'objects' ]:
        largest_domain = max(
            data[ 'domains' ].items( ), key = lambda x: x[ 1 ] )[ 0 ]
        sample_objects = data[ 'objects' ][ largest_domain ][ :5 ]
        lines.extend( [
            "",
            "Sample {domain} objects:".format( domain = largest_domain ),
        ] )
        lines.extend(
            "  {role}: {name}".format(
                role = obj[ 'role' ], name = obj[ 'name' ] )
            for obj in sample_objects )
    return '\n'.join( lines )


def _build_documentation_url(
    base_url: str, object_uri: str, object_name: str
) -> __.typx.Annotated[
    str, __.ddoc.Doc( ''' Full URL to documentation page for object. ''' )
]:
    ''' Constructs documentation URL from base URL and object URI. '''
    # Object URI format: "filename.html#anchor"
    # Example: "api.html#sphinxmcps.exceptions.InventoryFilterInvalidity"
    # Replace $ placeholder with actual object name
    uri_with_name = object_uri.replace( '$', object_name )
    return "{base_url}/{object_uri}".format(
        base_url = base_url.rstrip( '/' ), object_uri = uri_with_name )


def _collect_matching_objects(
    inventory: _sphobjinv.Inventory,
    domain: DomainFilter,
    role: RoleFilter,
    priority: PriorityFilter,
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
        try:
            pattern = __.re.compile( term, __.re.IGNORECASE )
            return lambda obj: bool( pattern.search( obj.name ) )
        except __.re.error as exc:
            message = f"Invalid regex pattern: {term}"
            raise _exceptions.InventoryFilterInvalidity( message ) from exc
    # Exact matching (default)
    term_lower = term.lower( )
    return lambda obj: term_lower in obj.name.lower( )


def _extract_inventory( source: SourceArgument ) -> __.typx.Annotated[
    _sphobjinv.Inventory,
    __.ddoc.Doc( ''' Parsed Sphinx inventory object. ''' )
]:
    ''' Extracts and parses Sphinx inventory from URL or file path. '''
    url = normalize_inventory_source( source )
    url_s = _urlparse.urlunparse( url )
    nomargs: __.NominativeArguments = { }
    match url.scheme:
        case 'http' | 'https': nomargs[ 'url' ] = url_s
        case 'file': nomargs[ 'fname_zlib' ] = url.path
        case _:
            raise _exceptions.InventoryUrlNoSupport(
                url, component = 'scheme', value = url.scheme )
    try: return _sphobjinv.Inventory( **nomargs )
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
        # Extract name from format like ":domain:role:`name`"
        if '`' in suggestion:
            name = suggestion.split( '`' )[ 1 ]  # Get text between backticks
            fuzzy_names.add( name )
    return fuzzy_names


def _filter_exact_and_regex_matching( # noqa: PLR0913
    inventory: _sphobjinv.Inventory,
    domain: DomainFilter,
    role: RoleFilter,
    priority: PriorityFilter,
    term: str,
    match_mode: _interfaces.MatchMode,
) -> tuple[ dict[ str, __.typx.Any ], int ]:
    ''' Filters inventory using exact or regex matching. '''
    term_matcher = _create_term_matcher( term, match_mode )
    return _collect_matching_objects(
        inventory, domain, role, priority, term_matcher )


def _filter_fuzzy_matching( # noqa: PLR0913
    inventory: _sphobjinv.Inventory,
    domain: DomainFilter,
    role: RoleFilter,
    priority: PriorityFilter,
    term: str,
    fuzzy_threshold: int,
) -> tuple[ dict[ str, __.typx.Any ], int ]:
    ''' Filters inventory using fuzzy matching via sphobjinv.suggest( ). '''
    suggestions = inventory.suggest( term, thresh = fuzzy_threshold )
    fuzzy_names = _extract_names_from_suggestions( suggestions )
    return _collect_matching_objects(
        inventory, domain, role, priority,
        lambda obj: obj.name in fuzzy_names )


def _filter_inventory( # noqa: PLR0913
    inventory: __.typx.Annotated[
        _sphobjinv.Inventory,
        __.ddoc.Doc( ''' Sphinx inventory object to filter. ''' )
    ],
    domain: DomainFilter = __.absent,
    role: RoleFilter = __.absent,
    term: TermFilter = __.absent,
    priority: PriorityFilter = __.absent,
    match_mode: MatchModeArgument = _interfaces.MatchMode.Exact,
    fuzzy_threshold: FuzzyThreshold = 50,
) -> __.typx.Annotated[
    tuple[ dict[ str, __.typx.Any ], int ],
    __.ddoc.Doc(
        ''' Filtered objects grouped by domain and total count.

            First element is a dictionary mapping domain names to lists of
            matching objects. Second element is the total number of objects
            that matched the filters.
        ''' )
]:
    ''' Filters inventory objects by domain, role, term, and match mode. '''
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
        'dispname': objct.dispname if objct.dispname != '-' else objct.name,
    }


def _extract_base_url( source: SourceArgument ) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( ''' Base URL for documentation from inventory source. ''' )
]:
    ''' Extracts base documentation URL from inventory source. '''
    url = normalize_inventory_source( source )
    path = url.path.rstrip( '/objects.inv' )
    if not path.endswith( '/' ): path += '/'
    return _urlparse.urlunparse(
        _urlparse.ParseResult(
            scheme = url.scheme, netloc = url.netloc, path = path,
            params = '', query = '', fragment = '' ) )


async def _fetch_html_content( url: str ) -> __.typx.Annotated[
    str, __.ddoc.Doc( ''' HTML content from documentation URL. ''' )
]:
    ''' Fetches HTML content from documentation URL or local file. '''
    parsed_url = _urlparse.urlparse( url )

    match parsed_url.scheme:
        case 'file':
            # Read from local filesystem
            try:
                file_path = __.Path( parsed_url.path )
                return file_path.read_text( encoding = 'utf-8' )
            except Exception as exc:
                raise _exceptions.DocumentationInaccessibility(
                    url, exc ) from exc
        case 'http' | 'https':
            # Fetch from web
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
                url, ValueError(
                    f"Unsupported URL scheme: {parsed_url.scheme}" )
            )


def _html_to_markdown( html_text: str ) -> str:
    ''' Converts HTML text to clean markdown format. '''
    if not html_text.strip( ):
        return ''

    try:
        soup = _BeautifulSoup( html_text, 'lxml' )
    except Exception:
        # Fallback to plain text if parsing fails
        return html_text

    # Convert common tags to markdown using replace_with
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
        if href:
            link.replace_with( f"[{text}]({href})" )
        else:
            link.replace_with( text )

    # Get clean text and normalize whitespace
    text = soup.get_text( )
    text = __.re.sub( r'\n\s*\n', '\n\n', text )
    text = __.re.sub( r'^\s+|\s+$', '', text, flags = __.re.MULTILINE )
    return text.strip( )


def normalize_inventory_source( source: SourceArgument ) -> __.typx.Annotated[
    _urlparse.ParseResult,
    __.ddoc.Doc(
        ''' Parsed URL components with objects.inv appended if needed.

            Ensures the path component ends with 'objects.inv' filename.
            Handles both URLs and local filesystem paths.
        ''' )
]:
    ''' Parses URL strings and appends objects.inv if needed. '''
    try: url = _urlparse.urlparse( source )
    except Exception as exc:
        raise _exceptions.InventoryUrlInvalidity( source ) from exc

    # Handle local filesystem paths by converting to file:// URLs
    match url.scheme:
        case '':
            # No scheme means local filesystem path
            path = __.Path( source ).resolve( )
            if path.is_dir( ):
                path = path / 'objects.inv'
            url = _urlparse.urlparse( path.as_uri( ) )
        case 'http' | 'https' | 'file':
            # Already a proper URL
            pass
        case _:
            raise _exceptions.InventoryUrlInvalidity( source )

    filename = 'objects.inv'
    if url.path.endswith( filename ): return url
    return _urlparse.ParseResult(
        scheme = url.scheme, netloc = url.netloc,
        path = f"{url.path}/{filename}",
        params = url.params, query = url.query, fragment = url.fragment )


def _parse_documentation_html(
    html_content: str,
    element_id: str
) -> __.typx.Annotated[
    __.cabc.Mapping[ str, str ],
    __.ddoc.Doc( ''' Parsed documentation sections. ''' )
]:
    ''' Parses HTML content to extract documentation sections. '''
    try: soup = _BeautifulSoup( html_content, 'lxml' )
    except Exception as exc:
        raise _exceptions.DocumentationParseFailure(
            element_id, exc ) from exc
    main_content = soup.find( 'article', { 'role': 'main' } )
    if not main_content:
        raise _exceptions.DocumentationContentAbsence( element_id )
    # Find the object definition by ID
    object_element = main_content.find( id = element_id )
    if not object_element:
        return { 'error': f"Object '{element_id}' not found in page" }
    # Extract signature and description based on element type
    if object_element.name == 'dt':
        # Function/class definition
        signature = object_element.get_text( strip = True )
        description_element = object_element.find_next_sibling( 'dd' )
        if description_element:
            # Remove header links and other navigation elements
            for header_link in description_element.find_all(
                'a', class_ = 'headerlink'
            ): header_link.decompose( )
            description = description_element.get_text( strip = True )
        else: description = ''
    elif object_element.name == 'section':
        # Module/package section
        header = object_element.find( [ 'h1', 'h2', 'h3', 'h4', 'h5', 'h6' ] )
        signature = header.get_text( strip = True ) if header else ''
        # Find the first paragraph after the header
        description_element = object_element.find( 'p' )
        if description_element:
            description = description_element.get_text( strip = True )
        else: description = ''
    else:
        # Generic element
        signature = object_element.get_text( strip = True )
        description = ''
    return {
        'signature': signature,
        'description': description,
        'object_name': element_id,
    }
