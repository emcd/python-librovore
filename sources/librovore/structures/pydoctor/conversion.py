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


class PydoctorMarkdownConverter( __.markdownify.MarkdownConverter ):
    ''' Custom markdownify converter for Pydoctor HTML. '''

    def convert_pre(
        self,
        el: __.typx.Any,
        text: str,
        convert_as_inline: bool,
    ) -> str:
        ''' Converts pre elements with Python code detection. '''
        if self.is_code_block( el ):
            # Pydoctor code blocks are typically Python
            code_text = el.get_text( )
            return f"\n```python\n{code_text}\n```\n"
        return super( ).convert_pre( el, text, convert_as_inline )

    def is_code_block( self, element: __.typx.Any ) -> bool:
        ''' Determines if element is a code block. '''
        # Pydoctor uses <pre> for code blocks
        return element.name == 'pre'


def html_to_markdown( html_text: str ) -> str:
    ''' Converts HTML text to markdown using Pydoctor-specific patterns. '''
    if not html_text.strip( ): return ''
    try: cleaned_html = _preprocess_pydoctor_html( html_text )
    except Exception: return html_text
    try:
        converter = PydoctorMarkdownConverter(
            heading_style = 'ATX',
            strip = [ 'nav', 'header', 'footer', 'script' ],
            escape_underscores = False,
            escape_asterisks = False
        )
        markdown = converter.convert( cleaned_html )
    except Exception: return html_text
    return markdown.strip( )


def _preprocess_pydoctor_html( html_text: str ) -> str:
    ''' Preprocesses Pydoctor HTML before markdown conversion. '''
    soup: __.typx.Any = _BeautifulSoup( html_text, 'lxml' )
    # Remove navigation elements
    for selector in [ '.navbar', '.sidebar', '.mainnavbar' ]:
        for element in soup.select( selector ):
            element.decompose( )
    # Remove search elements
    for selector in [ '#searchBox', '.search' ]:
        for element in soup.select( selector ):
            element.decompose( )
    # Remove Bootstrap scaffolding that doesn't contribute to content
    for selector in [ '.container', '.row', '.col-md-*' ]:
        for element in soup.select( selector ):
            # Unwrap instead of decompose to keep content
            element.unwrap( )
    return str( soup )
