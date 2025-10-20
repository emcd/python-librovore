.. vim: set fileencoding=utf-8:
.. -*- coding: utf-8 -*-
.. +--------------------------------------------------------------------------+
   |                                                                          |
   | Licensed under the Apache License, Version 2.0 (the "License");          |
   | you may not use this file except in compliance with the License.         |
   | You may obtain a copy of the License at                                  |
   |                                                                          |
   |     http://www.apache.org/licenses/LICENSE-2.0                           |
   |                                                                          |
   | Unless required by applicable law or agreed to in writing, software      |
   | distributed under the License is distributed on an "AS IS" BASIS,        |
   | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. |
   | See the License for the specific language governing permissions and      |
   | limitations under the License.                                           |
   |                                                                          |
   +--------------------------------------------------------------------------+


*******************************************************************************
Sphinx Themes HTML Structure Analysis
*******************************************************************************

**Objective**: Analyze Sphinx theme HTML structure to improve librovore content extraction and enable custom markdownify extensions for code blocks.

**Method**: Direct HTML download with curl + BeautifulSoup analysis to extract precise CSS selectors and structural patterns.

**Status**: ✅ ALL 8 THEMES ANALYZED | 🔥 **UNIVERSALLY CONSISTENT PATTERNS DISCOVERED!**

===============================================================================
Analysis Scripts
===============================================================================

**Location**: ``.auxiliary/scripts/mkdocs-analysis/``

Core Analysis Script: ``analyze_sphinx_html.py``
    Main analysis script using BeautifulSoup. Analyzes code blocks, API documentation, and section structure. Outputs ``analysis_results.json`` with detailed findings.

Helper Scripts
    - ``extract_code_patterns.py`` - Displays code block patterns from analysis results
    - ``section_analysis.py`` - Shows section structure and navigation patterns
    - ``comprehensive_summary.py`` - ✅ **COMPLETE ANALYSIS** of all 8 themes
    - ``download_remaining_themes.sh`` - Downloads all theme samples systematically

Usage
    .. code-block:: bash

        # Download samples
        curl -s "https://sphinx-themes.org/sample-sites/{theme}/kitchen-sink/blocks/" \
            -o .auxiliary/scribbles/sphinx-samples/{theme}-blocks.html

        # Run analysis
        hatch --env develop run python .auxiliary/scribbles/analyze_sphinx_html.py

        # View specific patterns
        hatch --env develop run python .auxiliary/scribbles/extract_code_patterns.py

===============================================================================
Key Findings
===============================================================================

1. Code Block Language Detection ✅ **SOLVED**
===============================================================================

**Critical Discovery**: Sphinx uses **parent container CSS classes** for language identification!

HTML Pattern
-------------------------------------------------------------------------------

.. code-block:: html

    <div class="highlight-python notranslate">
        <div class="highlight">
            <pre><!-- actual code content --></pre>
        </div>
    </div>

Language Identification
-------------------------------------------------------------------------------

Pattern: ``parent.class.startswith('highlight-')``

Languages found:
    - ``highlight-python`` - Python code blocks
    - ``highlight-json`` - JSON code blocks
    - ``highlight-text`` - Plain text blocks
    - ``highlight-default`` - Default/unknown language

Additional classes:
    - ``doctest`` - Python doctest blocks
    - ``notranslate`` - Prevents translation

2. API Documentation Structure ✅ **CONSISTENT**
===============================================================================

Pattern (Identical across Furo/RTD themes)
-------------------------------------------------------------------------------

API documentation structure:
    - Definition list: ``dl``
    - Signature element: ``dt.sig.sig-object.py``
    - Description element: ``dd``
    - Signature classes: ``['sig', 'sig-object', 'py']``
    - Anchor ID pattern: ``module.function_name``

HTML Structure
-------------------------------------------------------------------------------

.. code-block:: html

    <dl>
        <dt class="sig sig-object py" id="my_module.my_function">
            async my_module.my_function(parameter: ParameterT = default_value) → ReturnT¶
        </dt>
        <dd>
            The py:function directive.
        </dd>
    </dl>

3. Section Structure for Query Results ✅ **THEME-SPECIFIC**
===============================================================================

Furo Theme Patterns
-------------------------------------------------------------------------------

Furo section structure:
    - Main content: ``article[role="main"]``
    - Content wrapper: ``div.content``
    - Sections: ``section``
    - Extraction selectors (in priority order):
        1. ``article[role="main"] section`` (Primary)
        2. ``div.content section`` (Fallback)
        3. ``section`` (Generic)

RTD Theme Patterns
-------------------------------------------------------------------------------

RTD section structure:
    - Main wrapper: ``section.wy-nav-content-wrap``
    - Sections: ``section``
    - Navigation sidebar: ``nav.wy-nav-side``
    - Navigation top: ``nav.wy-nav-top``
    - Extraction selectors (in priority order):
        1. ``section.wy-nav-content-wrap section`` (Primary)
        2. ``section`` (Fallback)

===============================================================================
Complete Analysis Results - All 8 Themes
===============================================================================

✅ **UNIVERSAL CONSISTENCY DISCOVERED!**

**Themes Analyzed**: Furo, RTD, PyData, Python Documentation, Alabaster, agogo, classic, nature

Code Block Patterns - **100% CONSISTENT**
===============================================================================

Universal Classes Found Across ALL Themes
-------------------------------------------------------------------------------

.. code-block:: python

    code_block_classes = [
        'highlight',           # The actual code content container
        'highlight-default',   # Default/unknown language
        'highlight-python',    # Python syntax highlighting
        'highlight-json',      # JSON syntax highlighting
        'highlight-text',      # Plain text blocks
        'doctest',            # Python doctest blocks
        'notranslate'         # Prevents translation
    ]

HTML Pattern (IDENTICAL across all 8 themes)
-------------------------------------------------------------------------------

.. code-block:: html

    <div class="highlight-python notranslate">
        <div class="highlight">
            <pre><!-- code content --></pre>
        </div>
    </div>

API Documentation - **100% CONSISTENT**
===============================================================================

**Universal API Classes** (IDENTICAL across all 8 themes):

.. code-block:: python

    api_classes = ['sig', 'sig-object', 'py']

**Function Signatures**: All themes have exactly **19 function signatures** with identical structure.

Section Structure - **THEME-SPECIFIC BUT PREDICTABLE**
===============================================================================

Main Content Container Patterns
-------------------------------------------------------------------------------

.. code-block:: python

    section_extraction_priorities = {
        'furo': ['article[role="main"]', 'div.content', 'section'],
        'rtd': ['section.wy-nav-content-wrap', 'section'],
        'pydata': ['main.bd-main', 'article.bd-article', 'section'],
        'python-docs': ['div.body[role="main"]', 'section'],
        'alabaster': ['div.body[role="main"]', 'section'],
        'agogo': ['div.body[role="main"]', 'div.content', 'section'],
        'classic': ['div.body[role="main"]', 'section'],
        'nature': ['div.body[role="main"]', 'section'],
    }

Navigation Cleanup Patterns
-------------------------------------------------------------------------------

.. code-block:: python

    navigation_cleanup = {
        'rtd': ['nav.wy-nav-side', 'nav.wy-nav-top'],
        'pydata': ['nav.no-class', 'nav.bd-docs-nav', 'nav.d-print-none'],
        'python-docs': ['nav.menu', 'nav.nav-content'],
        'agogo': ['div.sidebar'],
        # Others use standard navigation patterns
    }

===============================================================================
Universal Sphinx Patterns Summary
===============================================================================

Code Blocks (100% consistent)


- **Selector**: ``.highlight``
- **Language detection**: ``parent_class_prefix:highlight-``
- **Supported languages**: ``['python', 'json', 'text', 'default']``
- **Additional classes**: ``['doctest', 'notranslate']``

API Documentation (100% consistent)


- **Signature selector**: ``dt.sig.sig-object.py``
- **Description selector**: ``dd``
- **Anchor pattern**: ``id_attribute``
- **Universal classes**: ``['sig', 'sig-object', 'py']``

Content Containers (Theme-specific)


.. code-block:: python

    content_containers = {
        'furo': ['article[role="main"]', 'div.content', 'section'],
        'sphinx_rtd_theme': ['section.wy-nav-content-wrap', 'section'],
        'pydata_sphinx_theme': ['main.bd-main', 'article.bd-article', 'section'],
        'python_docs_theme': ['div.body[role="main"]', 'section'],
        'alabaster': ['div.body[role="main"]', 'section'],
        'agogo': ['div.body[role="main"]', 'div.content', 'section'],
        'classic': ['div.body[role="main"]', 'section'],
        'nature': ['div.body[role="main"]', 'section'],
        'generic_fallback': [
            'div.body[role="main"]',
            'section',
            'div.content',
            'article[role="main"]'
        ]
    }

Navigation Cleanup (Theme-specific)


.. code-block:: python

    navigation_cleanup = {
        'sphinx_rtd_theme': ['nav.wy-nav-side', 'nav.wy-nav-top'],
        'pydata_sphinx_theme': ['nav.bd-docs-nav', 'nav.d-print-none'],
        'python_docs_theme': ['nav.menu', 'nav.nav-content'],
        'agogo': ['div.sidebar'],
        'generic': ['nav', '.navigation', '.sidebar', '.toc']
    }

===============================================================================
Final Summary
===============================================================================

✅ **MISSION ACCOMPLISHED!**

🔥 Universal Patterns Discovered


1. **Code Block Language Detection**: ``parent.class.startswith('highlight-')`` - **100% consistent across all 8 themes**
2. **API Documentation Structure**: ``dt.sig.sig-object.py + dd`` - **100% consistent across all 8 themes**
3. **Section Content Extraction**: Theme-specific selectors with predictable fallback patterns

Analysis Completeness


- **Themes Analyzed**: 8/8 (100%)
- **Code Block Consistency**: 100%
- **API Documentation Consistency**: 100%
- **Pattern Reliability**: Extremely High
- **Implementation Readiness**: Complete

Session Handoff Information


:Context: COMPLETE analysis of all 8 major Sphinx themes
:Status: ✅ **ANALYSIS COMPLETE** - All patterns discovered and documented
:Scripts: Comprehensive analysis toolchain in ``.auxiliary/scribbles/``
:Key Achievement: Discovered universal consistency in Sphinx theme structure
:Next Phase: Implementation in librovore structure extractors
