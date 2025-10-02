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
Theme Structure Research
*******************************************************************************

This section contains empirical research findings on the HTML structure and
patterns of documentation generation systems. These analyses inform the
content extraction strategies and structure processor implementations.

Research Methodology
===============================================================================

The research documented here was conducted through systematic analysis of
multiple documentation sites built with various themes:

- Direct HTML downloads using curl
- BeautifulSoup-based structural analysis
- Pattern extraction and consistency verification across themes
- CSS selector identification for reliable content targeting

Analysis scripts are preserved in ``.auxiliary/scripts/`` for reproducibility
and future validation.

===============================================================================
Theme Analysis Documents
===============================================================================

.. toctree::
   :maxdepth: 1

   sphinx-themes-elements
   mkdocs-themes-elements

Sphinx Themes
-------------------------------------------------------------------------------

Analysis of 8 major Sphinx themes revealing **100% consistent** patterns for:

- Code block language detection (``highlight-{lang}`` parent container classes)
- API documentation structure (``dt.sig.sig-object.py`` + ``dd`` patterns)
- Theme-specific content container selectors

The universal consistency across Sphinx themes enables highly reliable content
extraction for Sphinx-based documentation sites.

MkDocs Themes
-------------------------------------------------------------------------------

Analysis of 3 major MkDocs themes (Material, ReadTheDocs, default) across 10
representative documentation sites, discovering:

- Code block language detection (``language-{lang}`` element classes)
- mkdocstrings API documentation patterns (``div.autodoc-signature`` structure)
- Theme-specific content and navigation patterns

The mkdocstrings plugin provides Sphinx inventory compatibility with precise
function and class signature targeting capabilities.

===============================================================================
Implementation Impact
===============================================================================

The patterns documented in these research findings are implemented in:

Structure Processors
    Located in ``sources/librovore/structures/``, these processors use the
    documented CSS selectors and HTML patterns for reliable content extraction.

Markdownify Extensions
    Custom extensions leverage the language detection patterns to preserve code
    block formatting and metadata during HTML-to-Markdown conversion.

Theme Detection
    Automated theme identification enables selection of optimal extraction
    strategies based on documented patterns.

===============================================================================
Future Research
===============================================================================

Potential areas for additional analysis:

- Comparative analysis of custom Sphinx theme implementations
- MkDocs plugin ecosystem (beyond mkdocstrings)
- Jupyter Book and other Sphinx-derived documentation systems
- Version-specific theme variations and compatibility

As new documentation generation systems emerge, similar empirical analysis can
be conducted using the established methodology and analysis scripts.
