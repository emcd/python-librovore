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


def parse_documentation_html(
    content: str, element_id: str, *, theme: __.Absential[ str ] = __.absent
) -> __.cabc.Mapping[ str, str ]:
    ''' Parses HTML content to extract documentation sections. '''
    try: soup = _BeautifulSoup( content, 'lxml' )
    except Exception as exc:
        raise __.DocumentationParseFailure(
            element_id, exc ) from exc
    if __.is_absent( theme ):
        theme = _detect_theme_from_html( content )
    container = _find_main_content_container( soup, theme )
    if __.is_absent( container ):
        raise __.DocumentationContentAbsence( element_id )
    element = container.find( id = element_id )
    if not element:
        return { 'error': f"Object '{element_id}' not found in page" }
    if element.name == 'dt':
        signature, description = _extract_dt_content( element )
    elif element.name == 'section':
        signature, description = _extract_section_content( element )
    else:
        signature = element.get_text( strip = True )
        description = ''
    return {
        'signature': signature,
        'description': description,
        'object_name': element_id,
    }


def _detect_theme_from_html( content: str ) -> __.Absential[ str ]:
    ''' Detects theme from HTML content using CSS file patterns. '''
    content_l = content.lower( )
    theme_patterns = {
        'furo': [ 'furo', 'css/furo.css' ],
        'sphinx_rtd_theme': [ 'sphinx_rtd_theme', 'css/theme.css' ],
        'alabaster': [ 'alabaster', 'css/alabaster.css' ],
        'pydoctheme': [ 'pydoctheme.css', 'classic.css' ],
        'flask': [ 'flask.css' ],
        'nature': [ 'css/nature.css' ],
    }
    for theme_name, patterns in theme_patterns.items( ):
        if any( pattern in content_l for pattern in patterns ):
            return theme_name
    return __.absent


def _extract_dt_content( element: __.typx.Any ) -> tuple[ str, str ]:
    ''' Extracts signature and description from dt/dd elements. '''
    signature = element.get_text( strip = True )
    description_element = element.find_next_sibling( 'dd' )
    if description_element:
        for header_link in description_element.find_all(
            'a', class_ = 'headerlink'
        ): header_link.decompose( )
        description = description_element.get_text( strip = True )
    else: description = ''
    return signature, description


def _extract_section_content(
    element: __.typx.Any
) -> tuple[ str, str ]:
    ''' Extracts signature and description from section elements. '''
    header = element.find( [ 'h1', 'h2', 'h3', 'h4', 'h5', 'h6' ] )
    signature = header.get_text( strip = True ) if header else ''
    description_element = element.find( 'p' )
    if description_element:
        description = description_element.get_text( strip = True )
    else: description = ''
    return signature, description


def _find_main_content_container(
    soup: __.typx.Any, theme: __.Absential[ str ] = __.absent
) -> __.Absential[ __.typx.Any ]:
    ''' Finds the main content container using theme-specific strategies. '''
    if theme == 'furo':
        containers = [
            soup.find( 'article', { 'role': 'main' } ),
            soup.find( 'div', { 'id': 'furo-main-content' } ),
        ]
    elif theme == 'sphinx_rtd_theme':
        containers = [
            soup.find( 'div', { 'class': 'document' } ),
            soup.find( 'div', { 'class': 'body' } ),
            soup.find( 'div', { 'role': 'main' } ),
        ]
    elif theme == 'pydoctheme':  # Python docs
        containers = [
            soup.find( 'div', { 'class': 'body' } ),
            soup.find( 'div', { 'class': 'content' } ),
            soup.body,  # Python docs often use body directly
        ]
    elif theme == 'flask':  # Flask docs
        containers = [
            soup.find( 'div', { 'class': 'body' } ),
            soup.find( 'div', { 'class': 'content' } ),
            soup.body,
        ]
    elif theme == 'alabaster':
        containers = [
            soup.find( 'div', { 'class': 'body' } ),
            soup.find( 'div', { 'class': 'content' } ),
        ]
    else:  # Generic fallback for unknown themes
        containers = [
            soup.find( 'article', { 'role': 'main' } ),  # Furo theme
            soup.find( 'div', { 'class': 'body' } ),  # Basic theme
            soup.find( 'div', { 'class': 'content' } ),  # Nature theme
            soup.find( 'div', { 'class': 'main' } ),  # Generic main
            soup.find( 'main' ),  # HTML5 main element
            soup.find( 'div', { 'role': 'main' } ),  # Role-based
            soup.body,  # Fallback to body if nothing else works
        ]
    for container in containers:
        if container: return container
    return __.absent
