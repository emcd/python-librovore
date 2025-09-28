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


''' Universal MkDocs documentation patterns based on empirical analysis. '''


from . import __


UNIVERSAL_PATTERNS: __.cabc.Mapping[
    str, __.cabc.Mapping[ str, __.typx.Any ]
] = __.immut.Dictionary( {
    'code_blocks': __.immut.Dictionary( {
        'container_selector': '.highlight',
        'language_detection': __.immut.Dictionary( {
            'method': 'element_class_prefix',
            'prefix': 'language-',
            'language_map': __.immut.Dictionary( {
                'py': 'python',
                'js': 'javascript',
                'yml': 'yaml',
                'console': 'bash',
                'shell': 'bash',
                'bash': 'bash',
                'sh': 'bash',
                'python': 'python',
                'javascript': 'javascript',
                'yaml': 'yaml',
                'json': 'json',
            } ),
        } ),
    } ),
    'api_signatures': __.immut.Dictionary( {
        'mkdocstrings': __.immut.Dictionary( {
            'signature_container': 'div.autodoc',
            'signature_element': 'div.autodoc-signature',
            'docstring_element': 'div.autodoc-docstring',
            'function_name_selector': 'code > strong',
            'parameters_selector': 'em.autodoc-param',
            'signature_roles': [ 'function', 'class', 'method' ],
        } ),
    } ),
    'content_containers': __.immut.Dictionary( {
        'universal_selectors': [
            'main[role="main"]',
            'article[role="main"]',
        ],
        # 'generic_fallback': [
        #     'main', 'article', '[role="main"]', '.md-content', '.container'
        # ],
    } ),
    'navigation_cleanup': __.immut.Dictionary( {
        'universal_selectors': [
            'nav', '.navbar', '.navigation', '.sidebar'
        ],
    } ),
} )


THEME_PATTERNS: __.cabc.Mapping[
    str, __.cabc.Mapping[ str, __.cabc.Sequence[ str ] ]
] = __.immut.Dictionary( {
    'content_containers': __.immut.Dictionary( {
        'material': [
            'main.md-main', 'article.md-content__inner', 'div.md-content'
        ],
        'readthedocs': [ 'div.col-md-9[role="main"]', 'div.container' ],
        'mkdocs_default': [ 'div.col-md-9[role="main"]', 'div.container' ],
    } ),
    'navigation_cleanup': __.immut.Dictionary( {
        'material': [ 'nav.md-nav', 'div.md-sidebar', 'nav.md-header__inner' ],
        'readthedocs': [ 'div.navbar', 'ul.nav.navbar-nav' ],
        'mkdocs_default': [ 'div.navbar', 'ul.nav.navbar-nav' ],
    } ),
} )