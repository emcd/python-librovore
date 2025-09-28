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


from . import __

from .converters import convert_code_block_to_markdown as _convert_code_block


class SphinxMarkdownConverter( __.markdownify.MarkdownConverter ):
    ''' Custom markdownify converter for Sphinx using universal patterns. '''

    def convert_pre(
        self,
        el: __.typx.Annotated[
            __.typx.Any,
            __.ddoc.Doc( '''HTML pre element to convert.''' ),
        ],
        text: __.typx.Annotated[
            str,
            __.ddoc.Doc( '''Text content of the element.''' ),
        ],
        convert_as_inline: __.typx.Annotated[
            bool,
            __.ddoc.Doc( '''Whether to convert as inline element.''' ),
        ],
    ) -> __.typx.Annotated[
        str,
        __.ddoc.Doc( '''Converted markdown text.''' ),
    ]:
        ''' Converts pre elements with Sphinx code block detection. '''
        if self.is_code_block( el ):
            return _convert_code_block( el )
        return super( ).convert_pre( el, text, convert_as_inline )

    def is_code_block(
        self,
        element: __.typx.Annotated[
            __.typx.Any,
            __.ddoc.Doc( '''HTML element to check for code block.''' ),
        ],
    ) -> __.typx.Annotated[
        bool,
        __.ddoc.Doc( '''True if element represents a code block.''' ),
    ]:
        ''' Determines if element is a code block using universal patterns. '''
        classes = element.get( 'class', [ ] )
        if 'highlight' in classes: return True
        parent = element.parent
        if parent:
            parent_classes = parent.get( 'class', [ ] )
            for cls in parent_classes:
                if cls.startswith( 'highlight-' ): return True
        return False


def html_to_markdown(
    html_text: __.typx.Annotated[
        str,
        __.ddoc.Doc( '''HTML text to convert to markdown.''' ),
    ],
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( '''Converted markdown with Sphinx-specific processing.''' ),
]:
    ''' Converts HTML text to markdown using Sphinx-specific patterns. '''
    if not html_text.strip( ): return ''
    try: cleaned_html = _preprocess_sphinx_html( html_text )
    except Exception: return html_text
    try:
        converter = SphinxMarkdownConverter(
            heading_style = 'ATX',
            strip = [ 'nav', 'header', 'footer' ],
            escape_underscores = False,
            escape_asterisks = False
        )
        markdown = converter.convert( cleaned_html )
    except Exception: return html_text
    return markdown.strip( )


def html_to_markdown_sphinx(
    html_text: __.typx.Annotated[
        str,
        __.ddoc.Doc( '''HTML text to convert using Sphinx patterns.''' ),
    ],
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( '''Converted markdown text.''' ),
]:
    ''' Converts HTML to markdown using Sphinx universal patterns. '''
    return html_to_markdown( html_text )


def _preprocess_sphinx_html(
    html_text: __.typx.Annotated[
        str,
        __.ddoc.Doc( '''Raw HTML text to preprocess.''' ),
    ],
) -> __.typx.Annotated[
    str,
    __.ddoc.Doc( '''Cleaned HTML text ready for markdown conversion.''' ),
]:
    ''' Removes Sphinx-specific elements before markdownify processing. '''
    soup = __.bs4.BeautifulSoup( html_text, 'lxml' )
    # Remove headerlink elements (¶ symbols)
    for element in soup.find_all( class_ = 'headerlink' ):
        element.decompose( )
    return str( soup )
