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


''' Universal Sphinx documentation patterns based on empirical analysis. '''


from . import __


UNIVERSAL_PATTERNS: __.cabc.Mapping[
    str, __.cabc.Mapping[ str, __.typx.Any ]
] = __.immut.Dictionary( {
    'code_blocks': __.immut.Dictionary( {
        'container_selector': '.highlight',
        'language_detection': __.immut.Dictionary( {
            'method': 'parent_class_prefix',
            'prefix': 'highlight-',
            'language_map': __.immut.Dictionary( {
                'default': '',
                'text': '',
                'python': 'python',
                'json': 'json',
                'javascript': 'javascript',
                'bash': 'bash',
                'yaml': 'yaml',
                'py': 'python',
                'js': 'javascript',
                'sh': 'bash',
                'shell': 'bash',
                'console': 'bash',
                'yml': 'yaml',
            } ),
        } ),
    } ),
    'api_signatures': __.immut.Dictionary( {
        'signature_selector': 'dt.sig.sig-object.py',
        'description_selector': 'dd',
        'signature_classes': [ 'sig', 'sig-object', 'py' ],
        'signature_roles': [ 'function', 'class', 'method', 'attribute' ],
    } ),
    'content_containers': __.immut.Dictionary( {
        'universal_selectors': [
            'article[role="main"]',
            'main[role="main"]',
            'div.body[role="main"]',
        ],
        # 'generic_fallback': [
        #     'div.body[role="main"]', 'section', 'div.content',
        #     'article[role="main"]'
        # ],
    } ),
    'navigation_cleanup': __.immut.Dictionary( {
        'universal_selectors': [
            'nav', '.navigation', '.sidebar', '.toc', 'a.headerlink'
        ],
    } ),
} )


THEME_PATTERNS: __.cabc.Mapping[
    str, __.cabc.Mapping[ str, __.cabc.Sequence[ str ] ]
] = __.immut.Dictionary( {
    'content_containers': __.immut.Dictionary( {
        'furo': [ 'article[role="main"]', 'div.content', 'section' ],
        'sphinx_rtd_theme': [ 'section.wy-nav-content-wrap', 'section' ],
        'pydata_sphinx_theme': [
            'main.bd-main', 'article.bd-article', 'section'
        ],
        'python_docs_theme': [ 'div.body[role="main"]', 'section' ],
        'alabaster': [ 'div.body[role="main"]', 'section' ],
        'agogo': [ 'div.body[role="main"]', 'div.content', 'section' ],
        'classic': [ 'div.body[role="main"]', 'section' ],
        'nature': [ 'div.body[role="main"]', 'section' ],
    } ),
    'navigation_cleanup': __.immut.Dictionary( {
        'sphinx_rtd_theme': [ 'nav.wy-nav-side', 'nav.wy-nav-top' ],
        'pydata_sphinx_theme': [ 'nav.bd-docs-nav', 'nav.d-print-none' ],
        'python_docs_theme': [ 'nav.menu', 'nav.nav-content' ],
        'agogo': [ 'div.sidebar' ],
    } ),
} )