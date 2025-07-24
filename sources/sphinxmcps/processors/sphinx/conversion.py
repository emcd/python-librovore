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