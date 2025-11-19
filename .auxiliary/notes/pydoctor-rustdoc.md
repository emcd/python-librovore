# Pydoctor and Rustdoc Structure Analysis Plan

## Overview

This document outlines the reconnaissance and structural analysis needed to support Pydoctor and Rustdoc documentation sources in librovore, following the same approach used for Sphinx and MkDocs themes.

## Reference Sites

### Pydoctor

**Generator:** pydoctor (Python API documentation generator for projects using docstrings)

**Reference Sites:**
- **Dulwich API Documentation:** https://www.dulwich.io/api/
  - Uses: pydoctor 24.11.2
  - Theme: Bootstrap-based (bootstrap.min.css, apidocs.css)
  - Good example of: Module/package listing, class documentation, method signatures

- **Twisted API Documentation:** https://twisted.org/documents/current/api/
  - Uses: pydoctor (flagship project - pydoctor was originally developed for Twisted)
  - Large-scale example with extensive module hierarchy

- **Klein API Documentation:** https://klein.readthedocs.io/en/latest/api/ (if available)
  - Another pydoctor-based project

**Important Note:** https://pydoctor.readthedocs.io is built with Sphinx, NOT pydoctor itself.

### Rustdoc

**Generator:** rustdoc (official Rust documentation generator)

**Reference Sites:**
- **Rust Standard Library:** https://doc.rust-lang.org/std/
  - The canonical rustdoc example
  - Comprehensive coverage: modules, structs, traits, functions, macros

- **docs.rs:** https://docs.rs/ (e.g., https://docs.rs/serde/latest/serde/)
  - Hosts rustdoc for all published Rust crates
  - Good for variety of documentation styles

- **Rust Core Library:** https://doc.rust-lang.org/core/
  - Another official rustdoc example

**Themes:** Rustdoc has a single default theme with minimal variations (dark/light mode via CSS).

## Analysis Requirements

Based on the Sphinx and MkDocs analysis patterns, we need to understand:

### 1. Documentation Generator Detection

**Pydoctor:**
- Meta tag: `<meta name="generator" content="pydoctor X.Y.Z">`
- CSS indicators: `apidocs.css`, `pydoctor.js`
- DOM structure: Bootstrap-based navigation (`navbar navbar-default`)
- Specific elements: `.docstring`, `.itemName`, `.thingTitle`

**Rustdoc:**
- Meta tag: `<meta name="generator" content="rustdoc">`
- CSS indicators: `rustdoc-*.css`, `normalize-*.css`
- Custom elements: `<rustdoc-topbar>`, `<rustdoc-toolbar>`
- Meta data: `data-rustdoc-version`, `data-rustdoc-vars`

### 2. Theme Detection and Variations

**Pydoctor:**
- Primary theme: Bootstrap-based default theme
- CSS files to check:
  - `bootstrap.min.css` - Bootstrap framework
  - `apidocs.css` - Pydoctor-specific styles
  - `extra.css` - Project-specific customizations
- Note: Pydoctor has a single default theme with minor customizations possible

**Rustdoc:**
- Single canonical theme with color scheme variations
- CSS files to check:
  - `rustdoc-*.css` - Main rustdoc styles (versioned)
  - `normalize-*.css` - CSS normalization
  - `noscript-*.css` - Fallback styles
- Theme variants: Controlled via `data-themes` attribute
- No theme detection needed - one standard structure

### 3. HTML Structure Patterns

**Pydoctor:**

Content containers:
- Main navigation: `<nav class="navbar navbar-default mainnavbar">`
- Sidebar: `<nav class="sidebar">`
- Main content area: Body content (no specific wrapper)
- Module/class listings: `<div class="item">` with `.itemName`

API documentation elements:
- Module header: `<code class="thisobject">` in `.thingTitle`
- Docstrings: `<div class="docstring">`
- Signatures: Various inline code elements
- Methods/functions: Listed in sidebar and main content
- Inheritance info: Part of class documentation

Navigation patterns:
- Top navbar: Module/Class/Name indexes, search
- Sidebar: Hierarchical navigation of current module/package
- Search: Client-side JavaScript search

**Rustdoc:**

Content containers:
- Top bar: `<rustdoc-topbar>`
- Sidebar: `<nav class="sidebar">` with `.sidebar-elems`
- Main content: `<main>` > `.width-limiter` > `<section id="main-content" class="content">`
- Resizable sidebar: `<div class="sidebar-resizer">`

API documentation elements:
- Item declaration: `<pre class="rust item-decl">` with full type signature
- Documentation: `<div class="docblock">` (can be nested, multiple per page)
- Code examples: `<div class="example-wrap">` > `<pre class="rust">`
- Sections: `<details class="toggle">` with `.top-doc`
- Method listings: Sidebar `<section id="rustdoc-toc">` with categorized methods
- Trait implementations: Separate sections with impl blocks
- Source links: `<a class="src">` linking to source code

Navigation patterns:
- Sidebar navigation with search, module tree
- Section-based TOC for current page
- Breadcrumbs in main heading
- Custom elements: `<rustdoc-toolbar>` for page-level actions

### 4. Code Block Structure

**Pydoctor:**

Patterns to identify:
- Code blocks: `<pre>` elements (various classes)
- Inline code: `<code>` elements
- Constant values: `<pre class="constant-value">`
- Docstring code: Within `.docstring` divs
- Syntax highlighting: May use external highlighter or inline styles

Language detection:
- Typically Python (inferred from context)
- May include other languages in docstrings
- Check for class indicators on `<pre>` or parent elements

**Rustdoc:**

Patterns to identify:
- Code declarations: `<pre class="rust item-decl">`
- Example code: `<div class="example-wrap">` > `<pre class="rust">`
- Inline code: `<code>` elements
- Language classes: `.rust`, `.toml`, `.text`, etc.
- Ignored code: `.example-wrap.ignore`, `.example-wrap.compile_fail`
- Test indicators: `data-language` attribute

Language detection:
- Primary: Rust (`.rust` class)
- Others: TOML, text, console output
- Code fence info from parent `.example-wrap`

### 5. API Documentation Elements

**Pydoctor:**

Elements to extract:
- Module/package name: `<code class="thisobject">` in `.thingTitle`
- Class definitions: `.classDef` (if present)
- Function definitions: `.functionDef` (if present)
- Signatures: Inline code in headers
- Docstrings: `.docstring` divs (may contain formatted text, lists, code)
- Parameters: Within docstring (Sphinx-style or plain text)
- Return types: Type annotations in signatures
- Attributes: Listed in class documentation
- Inheritance: Base class information

Structure patterns:
- No `<dl>/<dt>/<dd>` structure like Sphinx
- Flatter organization with divs and classes
- Sidebar navigation for structure
- Docstrings contain all parameter/return documentation

**Rustdoc:**

Elements to extract:
- Item declarations: `<pre class="rust item-decl">` - full type signatures
- Descriptions: `<div class="docblock">` - Markdown-rendered documentation
- Code examples: Within `.example-wrap` (often multiple per item)
- Method sections: Organized by implementation type
- Trait implementations: Separate collapsible sections
- Type aliases: In item declaration
- Macro definitions: Special syntax in declarations
- Module documentation: Main `.docblock` at top
- Stability indicators: `<span class="since">`, `<span class="unstable">`
- Source links: `<a class="src">` - links to implementation

Structure patterns:
- Highly structured with semantic custom elements
- Heavy use of `<details>`/`<summary>` for collapsible content
- Clear separation of declaration vs documentation vs examples
- Comprehensive cross-referencing via links

### 6. Section and Heading Structure

**Pydoctor:**

Heading patterns:
- Page title: Often in `.thingTitle` with `<code>` element
- Subsections: Standard HTML headings (`<h1>`, `<h2>`, etc.)
- Limited section nesting in API docs

Section organization:
- Module overview at top
- Submodules/classes/functions listed
- Each item has its own page (or anchor on parent page)
- Minimal use of semantic `<section>` elements

**Rustdoc:**

Heading patterns:
- Main heading: `<h1>` in `.main-heading`
- Section headings: `<h2>`, `<h3>` with `.doc-anchor` for linkability
- TOC headings: Mirrored in sidebar
- Subsections: Nested within `.docblock`

Section organization:
- Main description in top-level `.docblock`
- Multiple sections: Examples, Implementations, Trait Impls, etc.
- Heavy use of `<details>` for collapsible sections
- Semantic `<section>` elements for main content areas
- Breadcrumb navigation

### 7. Search and Navigation Features

**Pydoctor:**

Search capabilities:
- Client-side JavaScript search
- Search box in main navbar
- Options: Search in docstrings toggle
- Search index: Likely JSON-based (check for `.js` files)
- Results display: Dynamic table insertion

Navigation aids:
- Module index (`moduleIndex.html`)
- Class index (`classIndex.html`)
- Name index (`nameIndex.html`)
- Breadcrumb-like navigation in sidebar
- Direct links to anchors for functions/methods

**Rustdoc:**

Search capabilities:
- Advanced client-side search
- Type-based search (can search by signature)
- Search data: `search-*.js`, `stringdex-*.js`
- Fuzzy matching, type inference
- Settings: `settings-*.js`

Navigation aids:
- Sidebar with collapsible module tree
- TOC for current page
- Breadcrumbs
- "All Items" link
- Keyboard shortcuts
- Direct source code links

## Reconnaissance Scripts to Create

Following the pattern from Sphinx/MkDocs analysis:

### 1. Download Scripts

**`.auxiliary/scripts/pydoctor-analysis/download_samples.sh`**
- Download from Dulwich: main page, module page, class page, function page
- Download from Twisted: representative samples
- Store in `.auxiliary/scribbles/pydoctor-samples/`

**`.auxiliary/scripts/rustdoc-analysis/download_samples.sh`**
- Download from Rust std: main, module, struct, trait, function, macro pages
- Download from docs.rs: 2-3 popular crates (serde, tokio, etc.)
- Store in `.auxiliary/scribbles/rustdoc-samples/`

### 2. Analysis Scripts

**`.auxiliary/scripts/pydoctor-analysis/analyze_pydoctor_html.py`**
- Detect generator and version
- Identify CSS theme files
- Extract main content container patterns
- Analyze navigation structure
- Code block identification
- API element patterns (docstrings, signatures)
- Output: JSON analysis file

**`.auxiliary/scripts/rustdoc-analysis/analyze_rustdoc_html.py`**
- Detect rustdoc version
- Identify custom elements (`<rustdoc-*>`)
- Extract content container patterns
- Analyze sidebar and TOC structure
- Code block and example patterns
- API element patterns (item-decl, docblock, impl blocks)
- Output: JSON analysis file

**Shared: `comprehensive_summary.py`**
- Compare Pydoctor vs Rustdoc patterns
- Identify universal extraction strategies
- Theme-specific handling requirements
- Integration recommendations for librovore

### 3. Pattern Extraction Scripts

**`extract_code_patterns.py`**
- Identify all code block variations
- Language detection mechanisms
- Syntax highlighting patterns
- Example code structure

**`extract_api_patterns.py`**
- Function/method signature formats
- Parameter documentation structure
- Return type documentation
- Type annotation handling
- Cross-reference link patterns

**`section_analysis.py`**
- Main content extraction selectors
- Navigation element identification
- Heading hierarchy analysis
- Section organization patterns

## Implementation Integration

### Detection Module

**`sources/librovore/structures/pydoctor/detection.py`**
```python
class PydoctorDetection(StructureDetection):
    source: str
    normalized_source: str = ''
    theme: Optional[str] = None  # Usually 'bootstrap-default'
    pydoctor_version: Optional[str] = None
```

Detection strategy:
- Check for `<meta name="generator" content="pydoctor">`
- Check for `apidocs.css` presence
- Check for `.docstring` class elements
- Confidence scoring based on multiple signals

**`sources/librovore/structures/rustdoc/detection.py`**
```python
class RustdocDetection(StructureDetection):
    source: str
    normalized_source: str = ''
    theme: str = 'default'  # Rustdoc has one theme
    rustdoc_version: Optional[str] = None
```

Detection strategy:
- Check for `<meta name="generator" content="rustdoc">`
- Check for `<rustdoc-topbar>` custom element
- Check for `data-rustdoc-version` attribute
- Very high confidence - rustdoc has unique markers

### Inventory Module

**Pydoctor:**
- **Sphinx-compatible inventory:** Optional - pydoctor can generate `objects.inv` but not by default
- **Primary inventory source:** `searchindex.json` (Lunr.js format)
  - Location: `{base_url}/searchindex.json`
  - Contains qualified names for all API objects
- **Alternative:** Parse HTML indexes (moduleIndex.html, classIndex.html, nameIndex.html)

**Rustdoc:**
- **No Sphinx-compatible inventory:** Rustdoc does not generate `objects.inv`
- **Primary inventory sources:**
  - "All Items" page: `/std/all.html` (or `/{crate}/all.html`)
  - Sidebar items: Per-module `sidebar-items{version}.js` files
  - Crates list: `crates{version}.js`
- **Recommended approach:** Parse "All Items" HTML page for complete inventory

### Extraction Module

**Content extraction priorities:**

Pydoctor:
1. Main content: Body content (no specific wrapper)
2. Docstrings: `.docstring` divs
3. Code examples: `<pre>` elements within docstrings
4. Signatures: Inline code in headers
5. Cleanup: Remove `.navbar`, `.sidebar`

Rustdoc:
1. Main content: `<main>` > `section#main-content`
2. Documentation: `.docblock` elements
3. Declarations: `.item-decl` elements
4. Code examples: `.example-wrap` > `pre.rust`
5. Cleanup: Remove `nav.sidebar`, `rustdoc-toolbar`, breadcrumbs

### Theme Support

**Pydoctor:**
- Single primary theme (Bootstrap-based)
- Focus on standard patterns
- Handle minor CSS customizations gracefully

**Rustdoc:**
- Single canonical structure
- No theme detection needed
- Color scheme variations don't affect structure
- Very consistent across versions

## Inventory/Index File Analysis

### Pydoctor Search Index Format

**File:** `searchindex.json` (Lunr.js index format)

**Structure:**
```json
{
  "version": "2.3.9",
  "fields": ["name", "names", "qname"],
  "fieldVectors": [
    ["name/dulwich", [0, 80.199]],
    ["names/dulwich", [0, 16.693]],
    ["qname/dulwich", [0, 26.733]],
    ["name/dulwich.repo", ...],
    ["qname/dulwich.repo.Repo", ...]
  ],
  ...
}
```

**Key characteristics:**
- Lunr.js search index (JavaScript search library)
- Vector-based for relevance scoring
- Fields: `name` (short name), `names` (tokenized), `qname` (qualified name)
- Qualified names like: `dulwich.repo.Repo`
- Large size (1-2MB+ for substantial projects)
- Secondary: `fullsearchindex.json` includes docstring content

**For librovore inventory:**
- Parse `searchindex.json` or `fullsearchindex.json`
- Extract qualified names from field vectors
- Map to module/class/function structure
- Fallback: Parse HTML indexes (moduleIndex.html, classIndex.html)

### Rustdoc Index Format

**Files:** Multiple per-crate JavaScript files

**Crates list:** `crates{version}.js`
```javascript
window.ALL_CRATES = ["alloc","core","proc_macro","std","std_detect","test"];
```

**Sidebar items:** `sidebar-items{version}.js` (per module)
```javascript
window.SIDEBAR_ITEMS = {
  "struct": ["Drain","ExtractIf","IntoIter","Vec"],
  "fn": ["from_elem", "from_raw_parts"],
  "macro": ["vec"]
};
```

**Key characteristics:**
- Distributed: One sidebar file per module
- Type-categorized: struct, enum, trait, fn, macro, etc.
- Simple format: Just names, not full signatures
- Small files (typically < 1KB per module)
- Version-stamped filenames

**For librovore inventory:**
- Option 1: Parse "All Items" page (`/std/all.html`)
  - Contains complete listing with links
  - Type annotations
  - Brief descriptions
- Option 2: Crawl sidebar-items files
  - Navigate module hierarchy
  - Collect items by type
  - Build qualified paths
- Option 3: Parse HTML structure
  - Very consistent semantic markup
  - Item declarations with full signatures
  - Comprehensive but requires HTML parsing

## Initial Investigation Steps

1. ✅ Download sample pages from reference sites
2. ✅ Run preliminary structure analysis
3. ✅ Identify and download search index files
4. ✅ Analyze inventory/index formats
5. ⏳ Create detailed analysis scripts (following Sphinx/MkDocs patterns)
6. ⏳ Extract code block patterns
7. ⏳ Extract API documentation patterns
8. ⏳ Extract section/navigation patterns
9. ⏳ Create comprehensive summary
10. ⏳ Design detection algorithms
11. ⏳ Design extraction strategies
12. ⏳ Implement in librovore

## Key Differences from Sphinx/MkDocs

### Pydoctor
- **Simpler structure:** No complex theme variations like Sphinx
- **Bootstrap-based:** More modern CSS framework
- **Flatter hierarchy:** Less nested DOM than Sphinx
- **JavaScript-heavy:** Client-side search and navigation
- **Python-specific:** Only Python APIs, simpler language detection
- **No inventory standard:** May need custom index parsing

### Rustdoc
- **Highly consistent:** One standard structure, minimal variation
- **Custom elements:** Uses Web Components (`<rustdoc-*>`)
- **Rich type information:** Complex type signatures in declarations
- **Example-heavy:** Code examples are first-class content
- **Source integration:** Direct links to source code
- **Search sophistication:** Type-aware search capabilities
- **Rust-specific:** Rust syntax, trait system, macro handling

## Expected Outcomes

1. **Detection confidence:**
   - Pydoctor: High (unique meta tag and CSS)
   - Rustdoc: Very high (unique custom elements)

2. **Extraction quality:**
   - Pydoctor: Good (straightforward structure)
   - Rustdoc: Excellent (highly semantic, consistent structure)

3. **Maintenance burden:**
   - Pydoctor: Low (stable structure, single theme)
   - Rustdoc: Very low (extremely stable, canonical structure)

4. **Integration complexity:**
   - Pydoctor: Medium (need custom inventory handling)
   - Rustdoc: Medium (need JavaScript search index parsing or HTML parsing)

## Next Steps

1. Run comprehensive structure analysis using scripts
2. Compare patterns with Sphinx/MkDocs findings
3. Document inventory/index formats
4. Create detection and extraction implementations
5. Test with diverse documentation sites
6. Integrate into librovore processor registry
