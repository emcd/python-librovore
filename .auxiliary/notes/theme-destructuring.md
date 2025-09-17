# Theme Pattern Destructuring and Universal Implementation

## Overview

Replace guesswork-based theme-specific patterns with empirically-discovered universal patterns from comprehensive theme analysis. This destructuring eliminates complexity while dramatically improving coverage and reliability.

## Analysis-Based Pattern Discovery

### Current State Assessment
- **Existing patterns**: Educated guesses covering 3-4 themes per processor
- **Analysis findings**: Universal patterns with 100% consistency across all themes
- **Coverage gap**: Missing 60%+ of real-world documentation themes

### Key Discovery: Pattern Universality
The comprehensive theme analysis revealed that apparent "theme-specific" variations are actually **surface-level CSS differences** over **universal underlying structures**.

## Universal Pattern Architecture

### Processor-Specific Implementation (Not Unified)
Rather than a shared universal dictionary, each processor should implement analysis-based patterns:

**Rationale for Separation**:
- Different detection mechanisms: Sphinx uses parent containers, MkDocs uses element classes
- Different signature structures: Sphinx uses `dt/dd`, MkDocs uses `div` containers
- Processor-specific optimizations and fallback strategies

### Sphinx Universal Patterns
```python
# sources/librovore/structures/sphinx/patterns.py
UNIVERSAL_SPHINX_PATTERNS = {
    'code_blocks': {
        'container_selector': '.highlight',
        'language_detection': {
            'method': 'parent_class_prefix',
            'prefix': 'highlight-',
            'language_map': {
                'default': '',
                'text': '',
                'python': 'python',
                'json': 'json',
                'javascript': 'javascript',
                'bash': 'bash',
                'yaml': 'yaml'
            }
        }
    },
    'api_signatures': {
        'signature_selector': 'dt.sig.sig-object.py',
        'description_selector': 'dd',
        'signature_classes': ['sig', 'sig-object', 'py'],
        'signature_roles': ['function', 'class', 'method', 'attribute']
    },
    'content_containers': {
        'universal_selectors': [
            'article[role="main"]',        # Semantic HTML5 with role
            'main[role="main"]',           # Explicit main role
            'div.body[role="main"]'        # Sphinx pattern with role
        ],
        'theme_specific_selectors': {
            'furo': ['article[role="main"]', 'div.content'],
            'sphinx_rtd_theme': ['section.wy-nav-content-wrap'],
            'pydata_sphinx_theme': ['main.bd-main', 'article.bd-article'],
            'python_docs_theme': ['div.body[role="main"]'],
            'alabaster': ['div.body[role="main"]'],
            'agogo': ['div.body[role="main"]', 'div.content'],
            'classic': ['div.body[role="main"]'],
            'nature': ['div.body[role="main"]']
        },
        'generic_fallbacks': ['main', 'div.body', 'div.content', 'section']
    },
    'navigation_cleanup': {
        'universal_selectors': [
            'nav', '.navigation', '.sidebar', '.toc',
            'a.headerlink'  # Universal Sphinx headerlinks
        ],
        'theme_specific_selectors': {
            'sphinx_rtd_theme': ['nav.wy-nav-side', 'nav.wy-nav-top'],
            'pydata_sphinx_theme': ['nav.bd-docs-nav', 'nav.d-print-none'],
            'python_docs_theme': ['nav.menu', 'nav.nav-content'],
            'agogo': ['div.sidebar']
        }
    }
}
```

### MkDocs Universal Patterns
```python
# sources/librovore/structures/mkdocs/patterns.py
UNIVERSAL_MKDOCS_PATTERNS = {
    'code_blocks': {
        'container_selector': '.highlight',
        'language_detection': {
            'method': 'element_class_prefix',
            'prefix': 'language-',
            'language_map': {
                'py': 'python',
                'js': 'javascript',
                'yml': 'yaml',
                'console': 'bash'
            }
        }
    },
    'api_signatures': {
        'mkdocstrings': {
            'signature_container': 'div.autodoc',
            'signature_element': 'div.autodoc-signature',
            'docstring_element': 'div.autodoc-docstring',
            'function_name_selector': 'code > strong',
            'parameters_selector': 'em.autodoc-param',
            'signature_roles': ['function', 'class', 'method']
        }
    },
    'content_containers': {
        'universal_selectors': [
            'main[role="main"]',           # Semantic main with role
            'article[role="main"]'         # Semantic article with role
        ],
        'theme_specific_selectors': {
            'material': ['main.md-main', 'article.md-content__inner', 'div.md-content'],
            'readthedocs': ['div.col-md-9[role="main"]', 'div.container'],
            'mkdocs_default': ['div.col-md-9[role="main"]', 'div.container']
        },
        'generic_fallbacks': ['main', 'article', '.md-content', '.container']
    },
    'navigation_cleanup': {
        'material': ['nav.md-nav', 'div.md-sidebar', 'nav.md-header__inner'],
        'readthedocs': ['div.navbar', 'ul.nav.navbar-nav'],
        'mkdocs_default': ['div.navbar', 'ul.nav.navbar-nav'],
        'generic': ['nav', '.navbar', '.navigation', '.sidebar']
    }
}
```

## Universal Pattern Implementation

### Code Block Language Detection Implementation

Based on the comprehensive analysis findings, implement language detection using the discovered universal patterns:

```python

class SphinxCodeBlockConverter:
    """Sphinx-specific code block conversion using universal patterns."""

    @staticmethod
    def convert_to_markdown(soup_element):
        """Convert Sphinx code block to markdown fenced code block."""
        language = SphinxCodeBlockConverter.extract_language(soup_element)
        code_content = soup_element.get_text()
        return f"```{language}\n{code_content}\n```"

    @staticmethod
    def extract_language(code_element):
        """Extract programming language from Sphinx code blocks using parent classes."""
        parent = code_element.parent
        if parent:
            classes = parent.get('class', [])
            for cls in classes:
                if cls.startswith('highlight-'):
                    language = cls.replace('highlight-', '')
                    return SphinxCodeBlockConverter._map_language(language)
        return ''

    @staticmethod
    def _map_language(sphinx_language):
        """Map Sphinx language names to standard markdown identifiers."""
        language_map = {
            'default': '', 'text': '', 'python': 'python',
            'json': 'json', 'javascript': 'javascript',
            'bash': 'bash', 'yaml': 'yaml'
        }
        return language_map.get(sphinx_language, sphinx_language)

class MkDocsCodeBlockConverter:
    """MkDocs-specific code block conversion using universal patterns."""

    @staticmethod
    def convert_to_markdown(soup_element):
        """Convert MkDocs code block to markdown fenced code block."""
        language = MkDocsCodeBlockConverter.extract_language(soup_element)
        code_content = soup_element.get_text()
        return f"```{language}\n{code_content}\n```"

    @staticmethod
    def extract_language(code_element):
        """Extract programming language from MkDocs code blocks using element classes."""
        classes = code_element.get('class', [])
        for cls in classes:
            if cls.startswith('language-'):
                language = cls.replace('language-', '')
                return MkDocsCodeBlockConverter._map_language(language)
        return ''

    @staticmethod
    def _map_language(mkdocs_language):
        """Map MkDocs language names to standard markdown identifiers."""
        language_map = {
            'py': 'python', 'js': 'javascript',
            'yml': 'yaml', 'console': 'bash'
        }
        return language_map.get(mkdocs_language, mkdocs_language)
```

### Signature Targeting Implementation

```python
def extract_sphinx_api_signatures(soup):
    """Extract API documentation using universal dt.sig.sig-object.py pattern."""
    api_objects = []

    for dt in soup.select('dt.sig.sig-object.py'):
        dd = dt.find_next_sibling('dd')
        if dd:
            api_objects.append({
                'signature': dt.get_text().strip(),
                'description': dd.get_text().strip(),
                'id': dt.get('id'),
                'type': 'function' if '(' in dt.get_text() else 'class'
            })

    return api_objects

def extract_mkdocstrings_signatures(soup):
    """Extract mkdocstrings signatures using div.autodoc-signature pattern."""
    signatures = []

    for autodoc in soup.select('div.autodoc'):
        signature_elem = autodoc.find('div', class_='autodoc-signature')
        docstring_elem = autodoc.find('div', class_='autodoc-docstring')

        if signature_elem:
            signature_info = {
                'type': 'class' if 'class ' in signature_elem.get_text() else 'function',
                'name': signature_elem.find('strong').get_text() if signature_elem.find('strong') else 'unknown',
                'signature': signature_elem.get_text().strip(),
                'docstring': docstring_elem.get_text().strip() if docstring_elem else '',
                'element': signature_elem,
                'container': autodoc
            }
            signatures.append(signature_info)

    return signatures
```

## Legacy Pattern Removal Strategy

### Current Patterns to Remove
```python
# Remove from sources/librovore/structures/sphinx/extraction.py
THEME_EXTRACTION_PATTERNS = {
    'pydoctheme': {...},  # Remove - replace with universal patterns
    'furo': {...},        # Remove - covered by universal selectors
    'sphinx_rtd_theme': {...},  # Remove - covered by universal selectors
}

# Remove from sources/librovore/structures/mkdocs/extraction.py
MATERIAL_THEME_PATTERNS = {
    'material': {...},      # Simplify to essential differences only
    'readthedocs': {...},   # Simplify to essential differences only
}
```

### Migration to Analysis-Based Patterns
1. **Replace guesswork**: All current theme patterns are educated guesses
2. **Use empirical data**: Patterns from systematic analysis of 11 themes
3. **Simplify logic**: Universal patterns eliminate complex theme detection
4. **Improve coverage**: From ~30% theme coverage to 100%

## Implementation Benefits

### Performance Improvements
- **Reduced CSS selectors**: From ~50 theme-specific selectors to ~5 universal ones
- **Faster detection**: Universal patterns eliminate theme-specific branching
- **Lower maintenance**: Single pattern set instead of per-theme maintenance

### Reliability Improvements
- **Empirical foundation**: Patterns based on actual analysis, not guesswork
- **Universal coverage**: Works across all analyzed themes and likely future ones
- **Signature precision**: Exact targeting for function/class documentation

### Architecture Alignment
- **Inventory-aware processing**: Signature extraction uses inventory object metadata and source attribution
- **Capability-based selection**: Processors advertise extraction capabilities including signatures
- **Fallback robustness**: Universal patterns provide reliable extraction across all themes

## Integration with Structure Processor Enhancement

The theme destructuring provides the empirical pattern foundation for the inventory-aware architecture described in structure-processor-enhancement.md:

### Pattern Integration Benefits
- **Universal Patterns Replace Guesswork**: Empirically-discovered patterns eliminate theme-specific complexity
- **Defensive Selector Strategy**: Content validation prevents false matches with generic selectors
- **Signature Targeting Precision**: Universal signature patterns enable reliable API object extraction
- **Code Block Language Preservation**: Language detection patterns maintain syntax highlighting information

### Architecture Alignment
- **Structure processors** implement universal patterns with inventory-aware strategy selection
- **Site-based selection** determines which processor handles the documentation site
- **Capability filtering** ensures only compatible inventory objects are processed
- **Strategy selection** uses inventory object metadata to choose optimal extraction methods

The comprehensive theme analysis provides the empirical foundation that makes inventory-aware processing reliable and performant across all documentation platforms.

## Summary

**Theme destructuring** eliminates guesswork-based complexity in favor of empirically-discovered universal patterns, while **inventory-aware extraction** uses object metadata to choose optimal strategies. Together they create a robust, performant, and maintainable extraction system that covers 100% of analyzed themes with enhanced reliability.

**Key Architecture Principles**:
1. **Site-Based Processor Selection**: One processor per site based on site detection confidence
2. **Capability-Based Object Filtering**: Only process objects the selected processor supports
3. **Universal Pattern Foundation**: Empirical patterns replace theme-specific guesswork
4. **Inventory-Aware Strategy Selection**: Use object metadata to choose extraction methods