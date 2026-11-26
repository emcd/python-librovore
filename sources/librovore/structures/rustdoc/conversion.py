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


''' HTML to Markdown conversion for Rustdoc content. '''


from markdownify import markdownify as _md

from . import __


def convert_to_markdown( html: str ) -> str:
    ''' Converts Rustdoc HTML to Markdown format. '''
    if not html or not html.strip( ):
        return ''
    markdown = _md(
        html,
        heading_style = 'ATX',
        code_language = 'rust',
        strip = [ 'nav', 'aside', 'header', 'footer' ],
    )
    return markdown.strip( )


def extract_code_language( element: __.typx.Any ) -> str:
    ''' Extracts code language from Rustdoc HTML element classes. '''
    classes = element.get( 'class', [ ] )
    if not classes: return 'rust'
    for cls in classes:
        if cls in ( 'rust', 'toml', 'text', 'console', 'sh', 'bash' ):
            return cls
    return 'rust'
