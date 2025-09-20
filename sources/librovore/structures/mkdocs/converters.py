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


''' MkDocs-specific code block converters for universal pattern system. '''


from . import __
from .patterns import UNIVERSAL_PATTERNS as _UNIVERSAL_PATTERNS


def convert_code_block_to_markdown( soup_element: __.typx.Any ) -> str:
    ''' Converts code block to markdown fenced code block. '''
    language = extract_code_language( soup_element )
    code_content = soup_element.get_text( )
    return f"```{language}\n{code_content}\n```"


def extract_code_language( code_element: __.typx.Any ) -> str:
    ''' Extracts programming language from code blocks. '''
    classes = code_element.get( 'class', [ ] )
    language_config = _UNIVERSAL_PATTERNS[ 'code_blocks' ][
        'language_detection'
    ]
    prefix = language_config[ 'prefix' ]
    language_map = language_config[ 'language_map' ]
    for cls in classes:
        if cls.startswith( prefix ):
            language = cls.replace( prefix, '' )
            return _map_language( language, language_map )
    return ''


def _map_language(
    language: str,
    language_map: __.cabc.Mapping[ str, str ]
) -> str:
    ''' Maps language names to standard markdown identifiers. '''
    return language_map.get( language, language )