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
    context = _MarkdownContext( )
    result = _convert_element_to_markdown( soup, context )
    return _clean_whitespace( result )


class _MarkdownContext:
    ''' Context for tracking state during HTML-to-Markdown conversion. '''
    pass


def _convert_element_to_markdown(
    element: __.typx.Any, context: _MarkdownContext
) -> str:
    ''' Converts HTML element to markdown using single-pass traversal. '''
    if hasattr( element, 'name' ) and element.name:
        return _convert_tag_to_markdown( element, context )
    # Text node - preserve spacing as-is
    return str( element )


def _convert_tag_to_markdown(  # noqa: PLR0911
    element: __.typx.Any, context: _MarkdownContext
) -> str:
    ''' Converts HTML tag to markdown using pattern matching. '''
    match element.name:
        case 'code':
            return '`{}`'.format( element.get_text( ) )
        case 'pre':
            return '```\n{}\n```'.format( element.get_text( ) )
        case 'strong':
            children = _convert_children( element, context )
            return '**{}**'.format( children )
        case 'em':
            children = _convert_children( element, context )
            return '*{}*'.format( children )
        case 'a':
            return _convert_link( element, context )
        case 'span':
            # Inline span - just return the content, spacing handled by parent
            return _convert_children( element, context )
        case 'p' | 'div' | 'section' | 'article' | 'li' | 'dt' | 'dd':
            children = _convert_children( element, context )
            return '{}\n\n'.format( children ) if children.strip( ) else ''
        case 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6':
            return _convert_header( element, context )
        case 'br':
            return '\n'
        case _:
            # Skip navigation elements
            if _is_navigation_element( element ):
                return ''
            return _convert_children( element, context )


def _convert_children(
    element: __.typx.Any, context: _MarkdownContext
) -> str:
    ''' Converts all child elements to markdown. '''
    result_parts: list[ str ] = [ ]
    for child in element.children:
        converted = _convert_element_to_markdown( child, context )
        result_parts.append( converted )  # Preserve spacing
    return ''.join( result_parts )


def _convert_link( element: __.typx.Any, context: _MarkdownContext ) -> str:
    ''' Converts anchor element to markdown link. '''
    href = element.get( 'href', '' )
    text = element.get_text( )
    if href:
        return '[{}]({})'.format( text, href )
    return text


def _convert_header( element: __.typx.Any, context: _MarkdownContext ) -> str:
    ''' Converts header element to markdown. '''
    text = element.get_text( strip = True )
    return '{}\n\n'.format( text ) if text else ''


def _is_navigation_element( element: __.typx.Any ) -> bool:
    ''' Checks if element should be skipped as navigation. '''
    if element.get( 'class' ):
        classes = element.get( 'class' )
        if isinstance( classes, list ) and 'headerlink' in classes:
            return True
    return False


def _clean_whitespace( text: str ) -> str:
    ''' Cleans up whitespace while preserving paragraph structure. '''
    text = __.re.sub( r' +', ' ', text )
    text = __.re.sub( r'\n +', '\n', text )
    text = __.re.sub( r' +\n', '\n', text )
    text = __.re.sub( r'\n{3,}', '\n\n', text )
    # Remove leading/trailing spaces on lines, but NOT newlines
    text = __.re.sub( r'^[ \t]+|[ \t]+$', '', text, flags = __.re.MULTILINE )
    return text.strip( )