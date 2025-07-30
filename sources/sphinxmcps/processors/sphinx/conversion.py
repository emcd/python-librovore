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


''' HTML to markdown conversion utilities. '''


from bs4 import BeautifulSoup as _BeautifulSoup

from . import __


def html_to_markdown( html_text: str ) -> str:
    ''' Converts HTML text to clean markdown format with proper paragraphs. '''
    if not html_text.strip( ): return ''
    try: soup = _BeautifulSoup( html_text, 'lxml' )
    except Exception: return html_text
    _clean_navigation_elements( soup )
    _process_inline_elements( soup )
    _add_paragraph_separators( soup )
    # Extract text with unique separator that we can replace later
    separator = '***PARAGRAPH_BREAK***'
    text = soup.get_text( separator = separator )
    # Replace our separator with actual paragraph breaks
    text = text.replace( separator, '\n\n' )
    return _clean_whitespace( text )


def _process_inline_elements( soup: _BeautifulSoup ) -> None:
    ''' Processes inline HTML elements for markdown conversion. '''
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


def _add_paragraph_separators( soup: _BeautifulSoup ) -> None:
    ''' Adds paragraph separators after block elements. '''
    block_elements = [
        'p', 'div', 'section', 'article', 'li', 'dt', 'dd',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6' ]
    
    # Replace each block element with its text plus unique separator
    separator = '***PARAGRAPH_BREAK***'
    for element_name in block_elements:
        for element in soup.find_all( element_name ):
            element_text = element.get_text( strip = True )
            if element_text:
                # Replace with text plus separator
                element.replace_with( element_text + separator )


def _clean_navigation_elements( soup: _BeautifulSoup ) -> None:
    ''' Removes navigation and header link elements. '''
    for header_link in soup.find_all( 'a', class_ = 'headerlink' ):
        header_link.decompose( )


def _clean_whitespace( text: str ) -> str:
    ''' Cleans up whitespace while preserving paragraph structure. '''
    text = __.re.sub( r' +', ' ', text )
    text = __.re.sub( r'\n +', '\n', text )
    text = __.re.sub( r' +\n', '\n', text )
    text = __.re.sub( r'\n{3,}', '\n\n', text )
    # Remove leading/trailing spaces on lines, but NOT newlines
    text = __.re.sub( r'^[ \t]+|[ \t]+$', '', text, flags = __.re.MULTILINE )
    return text.strip( )