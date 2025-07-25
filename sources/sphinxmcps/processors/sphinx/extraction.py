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


''' Documentation extraction and content retrieval. '''


from bs4 import BeautifulSoup as _BeautifulSoup

from . import __


def calculate_relevance_score(
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


def extract_content_snippet(
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


def parse_documentation_html(
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
