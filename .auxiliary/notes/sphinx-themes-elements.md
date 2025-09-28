# Sphinx Themes HTML Structure Analysis

**Objective**: Analyze Sphinx theme HTML structure to improve librovore content extraction and enable custom markdownify extensions for code blocks.

**Method**: Direct HTML download with curl + BeautifulSoup analysis to extract precise CSS selectors and structural patterns.

**Status**: ✅ ALL 8 THEMES ANALYZED | 🔥 **UNIVERSALLY CONSISTENT PATTERNS DISCOVERED!**

---

## Analysis Scripts

**Location**: `.auxiliary/scribbles/`

### Core Analysis Script: `analyze_sphinx_html.py`
```python
# Main analysis script using BeautifulSoup
# Analyzes: code blocks, API documentation, section structure
# Outputs: analysis_results.json with detailed findings
```

### Helper Scripts:
- `extract_code_patterns.py` - Displays code block patterns from analysis results
- `section_analysis.py` - Shows section structure and navigation patterns
- `comprehensive_summary.py` - ✅ **COMPLETE ANALYSIS** of all 8 themes
- `download_remaining_themes.sh` - Downloads all theme samples systematically

### Usage:
```bash
# Download samples
curl -s "https://sphinx-themes.org/sample-sites/{theme}/kitchen-sink/blocks/" -o .auxiliary/scribbles/sphinx-samples/{theme}-blocks.html

# Run analysis
hatch --env develop run python .auxiliary/scribbles/analyze_sphinx_html.py

# View specific patterns
hatch --env develop run python .auxiliary/scribbles/extract_code_patterns.py
```

---

## Key Findings

### 1. Code Block Language Detection ✅ **SOLVED**

**Critical Discovery**: Sphinx uses **parent container CSS classes** for language identification!

**HTML Pattern**:
```html
<div class="highlight-python notranslate">
    <div class="highlight">
        <pre><!-- actual code content --></pre>
    </div>
</div>
```

**Language Identification**:
```python
# Pattern: parent.class.startswith('highlight-')
languages_found = [
    'highlight-python',    # Python code blocks
    'highlight-json',      # JSON code blocks
    'highlight-text',      # Plain text blocks
    'highlight-default'    # Default/unknown language
]

additional_classes = [
    'doctest',       # Python doctest blocks
    'notranslate'    # Prevents translation
]
```

**Implementation for Markdownify Extension**:
```python
def extract_code_language(code_element):
    """Extract programming language from Sphinx code blocks."""
    parent = code_element.parent
    if parent:
        classes = parent.get('class', [])
        for cls in classes:
            if cls.startswith('highlight-'):
                language = cls.replace('highlight-', '')
                # Map Sphinx languages to standard markdown
                language_map = {
                    'default': '',
                    'text': '',
                    'python': 'python',
                    'json': 'json',
                    'javascript': 'javascript',
                    'c': 'c',
                    'cpp': 'cpp'
                }
                return language_map.get(language, language)
    return ''

def convert_to_markdown_codeblock(soup_element):
    """Convert Sphinx code block to markdown fenced code block."""
    language = extract_code_language(soup_element)
    code_content = soup_element.get_text()
    return f"```{language}\n{code_content}\n```"
```

### 2. API Documentation Structure ✅ **CONSISTENT**

**Pattern** (Identical across Furo/RTD themes):
```python
api_documentation_structure = {
    'definition_list': 'dl',
    'signature_element': 'dt.sig.sig-object.py',
    'description_element': 'dd',
    'signature_classes': ['sig', 'sig-object', 'py'],
    'anchor_id_pattern': 'module.function_name'
}
```

**HTML Structure**:
```html
<dl>
    <dt class="sig sig-object py" id="my_module.my_function">
        async my_module.my_function(parameter: ParameterT = default_value) → ReturnT¶
    </dt>
    <dd>
        The py:function directive.
    </dd>
</dl>
```

**Implementation**:
```python
def extract_api_objects(soup):
    """Extract API documentation objects."""
    api_objects = []

    for dt in soup.select('dt.sig.sig-object'):
        dd = dt.find_next_sibling('dd')
        if dd:
            api_objects.append({
                'signature': dt.get_text().strip(),
                'description': dd.get_text().strip(),
                'id': dt.get('id'),
                'type': 'function' if '(' in dt.get_text() else 'class'
            })

    return api_objects
```

### 3. Section Structure for Query Results ✅ **THEME-SPECIFIC**

**Furo Theme Patterns**:
```python
furo_section_structure = {
    'main_content': 'article[role="main"]',
    'content_wrapper': 'div.content',
    'sections': 'section',
    'extraction_selectors': [
        'article[role="main"] section',  # Primary
        'div.content section',           # Fallback
        'section'                        # Generic
    ]
}
```

**RTD Theme Patterns**:
```python
rtd_section_structure = {
    'main_wrapper': 'section.wy-nav-content-wrap',
    'sections': 'section',
    'navigation_sidebar': 'nav.wy-nav-side',
    'navigation_top': 'nav.wy-nav-top',
    'extraction_selectors': [
        'section.wy-nav-content-wrap section',  # Primary
        'section'                               # Fallback
    ]
}
```

**Implementation**:
```python
def extract_content_sections(soup, theme='auto'):
    """Extract main content sections for query results."""

    selectors = {
        'furo': [
            'article[role="main"] section',
            'div.content section',
            'section'
        ],
        'rtd': [
            'section.wy-nav-content-wrap section',
            'section'
        ],
        'generic': [
            'article[role="main"]',
            'div.content',
            'section',
            '.body'
        ]
    }

    theme_selectors = selectors.get(theme, []) + selectors['generic']

    for selector in theme_selectors:
        sections = soup.select(selector)
        if sections:
            return [section for section in sections
                   if len(section.find_all('p')) > 0]  # Must have content

    return []
```

---

## 🔥 COMPLETE ANALYSIS RESULTS - ALL 8 THEMES

### ✅ **UNIVERSAL CONSISTENCY DISCOVERED!**

**Themes Analyzed**: Furo, RTD, PyData, Python Documentation, Alabaster, agogo, classic, nature

### 🎯 Code Block Patterns - **100% CONSISTENT**

**Universal Classes Found Across ALL Themes**:
```python
code_block_classes = [
    'highlight',           # The actual code content container
    'highlight-default',   # Default/unknown language
    'highlight-python',    # Python syntax highlighting
    'highlight-json',      # JSON syntax highlighting
    'highlight-text',      # Plain text blocks
    'doctest',            # Python doctest blocks
    'notranslate'         # Prevents translation
]
```

**HTML Pattern** (IDENTICAL across all 8 themes):
```html
<div class="highlight-python notranslate">
    <div class="highlight">
        <pre><!-- code content --></pre>
    </div>
</div>
```

### 🎯 API Documentation - **100% CONSISTENT**

**Universal API Classes** (IDENTICAL across all 8 themes):
```python
api_classes = ['sig', 'sig-object', 'py']
```

**Function Signatures**: All themes have exactly **19 function signatures** with identical structure

### 🎯 Section Structure - **THEME-SPECIFIC BUT PREDICTABLE**

**Main Content Container Patterns**:
```python
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
```

**Navigation Cleanup Patterns**:
```python
navigation_cleanup = {
    'rtd': ['nav.wy-nav-side', 'nav.wy-nav-top'],
    'pydata': ['nav.no-class', 'nav.bd-docs-nav', 'nav.d-print-none'],
    'python-docs': ['nav.menu', 'nav.nav-content'],
    'agogo': ['div.sidebar'],
    # Others use standard navigation patterns
}
```

---

---

## Implementation Guidance

### For Structure Extractors (`@sources/librovore/structures/`)

**🔥 COMPREHENSIVE EXTRACTION PATTERNS - ALL 8 THEMES**:
```python
UNIVERSAL_SPHINX_PATTERNS = {
    # Universal code block pattern (100% consistent)
    'code_blocks': {
        'selector': '.highlight',
        'language_detection': 'parent_class_prefix:highlight-',
        'supported_languages': ['python', 'json', 'text', 'default'],
        'additional_classes': ['doctest', 'notranslate']
    },

    # Universal API documentation pattern (100% consistent)
    'api_documentation': {
        'signature_selector': 'dt.sig.sig-object.py',
        'description_selector': 'dd',
        'anchor_pattern': 'id_attribute',
        'universal_classes': ['sig', 'sig-object', 'py']
    },

    # Theme-specific content containers
    'content_containers': {
        'furo': ['article[role="main"]', 'div.content', 'section'],
        'sphinx_rtd_theme': ['section.wy-nav-content-wrap', 'section'],
        'pydata_sphinx_theme': ['main.bd-main', 'article.bd-article', 'section'],
        'python_docs_theme': ['div.body[role="main"]', 'section'],
        'alabaster': ['div.body[role="main"]', 'section'],
        'agogo': ['div.body[role="main"]', 'div.content', 'section'],
        'classic': ['div.body[role="main"]', 'section'],
        'nature': ['div.body[role="main"]', 'section'],
        'generic_fallback': ['div.body[role="main"]', 'section', 'div.content', 'article[role="main"]']
    },

    # Theme-specific navigation cleanup
    'navigation_cleanup': {
        'sphinx_rtd_theme': ['nav.wy-nav-side', 'nav.wy-nav-top'],
        'pydata_sphinx_theme': ['nav.bd-docs-nav', 'nav.d-print-none'],
        'python_docs_theme': ['nav.menu', 'nav.nav-content'],
        'agogo': ['div.sidebar'],
        'generic': ['nav', '.navigation', '.sidebar', '.toc']
    }
}
```

### For Markdownify Extension

**Code Block Conversion**:
- Use `parent.class.startswith('highlight-')` for language detection
- Map Sphinx language names to standard markdown language identifiers
- Preserve doctest patterns for Python examples

**Content Section Extraction**:
- Use theme-aware selectors with generic fallbacks
- Filter sections that contain actual content (paragraphs)
- Clean up navigation and sidebar elements

---

## 🎯 FINAL SUMMARY

### ✅ **MISSION ACCOMPLISHED!**

**🔥 UNIVERSAL PATTERNS DISCOVERED**:
1. **Code Block Language Detection**: `parent.class.startswith('highlight-')` - **100% consistent across all 8 themes**
2. **API Documentation Structure**: `dt.sig.sig-object.py + dd` - **100% consistent across all 8 themes**
3. **Section Content Extraction**: Theme-specific selectors with predictable fallback patterns

### 🚀 **READY FOR IMPLEMENTATION**

**For Librovore Structure Extractors**:
- ✅ Universal code block language detection
- ✅ Universal API documentation extraction
- ✅ Theme-aware content section selection
- ✅ Comprehensive navigation cleanup patterns

**For Custom Markdownify Extension**:
- ✅ Precise language detection for fenced code blocks
- ✅ Complete CSS class to language mapping
- ✅ Doctest and special block handling

### 📊 **ANALYSIS COMPLETENESS**
- **Themes Analyzed**: 8/8 (100%)
- **Code Block Consistency**: 100%
- **API Documentation Consistency**: 100%
- **Pattern Reliability**: Extremely High
- **Implementation Readiness**: Complete

## Session Handoff Information

**Context**: COMPLETE analysis of all 8 major Sphinx themes
**Status**: ✅ **ANALYSIS COMPLETE** - All patterns discovered and documented
**Scripts**: Comprehensive analysis toolchain in `.auxiliary/scribbles/`
**Key Achievement**: Discovered universal consistency in Sphinx theme structure
**Next Phase**: Implementation in librovore structure extractors