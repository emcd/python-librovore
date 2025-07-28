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


''' Docstrings table for reuse across entities. '''


from . import imports as __


def access_doctab( name: str ) -> str:
    ''' Returns cleaned string corresponding to fragment. '''
    return __.inspect.cleandoc( fragments[ name ] )


fragments: __.cabc.Mapping[ str, str ] = __.types.MappingProxyType( {

    'domain filter argument':
    ''' Filter objects by domain.

        A domain is a category of objects in the site inventory.

        E.g., built-in domains for Sphinx:
        'py' (Python), 'std' (standard), 'c' (C), 'cpp' (C++),
        'js' (JavaScript), 'rst' (reStructuredText),
        'math' (Mathematics)

        Empty string shows all domains.
    ''',

    'fuzzy threshold argument':
    ''' Fuzzy-matching threshold.

        Range 0 to 100. Higher is stricter.
    ''',

    'query details argument':
    ''' Detail level for inventory results (Name, Signature, Summary, 
        Documentation). ''',

    'include snippets argument':
    ''' Include content snippets in results. ''',

    'match mode argument':
    ''' Term matching mode: exact, regex, or fuzzy. ''',

    'match mode cli argument':
    ''' Term matching mode: Exact, Regex, or Fuzzy. ''',

    'objects max argument':
    ''' Maximum number of objects to process. ''',

    'results max argument':
    ''' Maximum number of results to return. ''',

    'object name':
    ''' Name of the object to extract documentation for. ''',

    'priority filter argument':
    ''' Filter objects by priority level (e.g., '1', '0'). ''',

    'query argument':
    ''' Search query for documentation content. ''',

    'role filter argument':
    ''' Filter objects by role (e.g., 'function'). ''',

    'section filter argument':
    ''' Sections to include (signature, description). ''',

    'server port argument':
    ''' TCP port for server. ''',

    'source argument':
    ''' URL or file path to documentation source. ''',

    'term filter argument':
    ''' Filter objects by name containing this text. ''',

    'transport argument':
    ''' Transport: stdio or sse. ''',

    'documentation return':
    ''' Search results with metadata in explore format. ''',

    'explore return':
    ''' Combined inventory search and documentation extraction returns.
        Contains search metadata, matching objects, successful documentation
        extractions, and any errors encountered.
    ''',

    'inventory summary return':
    ''' Human-readable summary of inventory contents. ''',

    'inventory query return':
    ''' Inventory search results with configurable detail levels.
        Contains project metadata, matching objects, and search metadata
        with applied filters.
    ''',

    'content query return':
    ''' Documentation content search results with relevance ranking.
        Contains documents with signatures, descriptions, content snippets,
        relevance scores, and match reasons.
    ''',

} )
