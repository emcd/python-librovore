# Pydoctor and Rustdoc Analysis - Outstanding Questions

## Status: COMPLETE ✅

All initial reconnaissance and analysis planning is complete. The following items are ready for implementation:

## Completed Research

1. ✅ **Reference sites identified**
   - Pydoctor: Dulwich, Twisted
   - Rustdoc: Rust std library, docs.rs (serde, tokio)

2. ✅ **Generator detection patterns identified**
   - Pydoctor: `<meta name="generator" content="pydoctor">`, CSS files, DOM structure
   - Rustdoc: `<meta name="generator" content="rustdoc">`, custom elements, data attributes

3. ✅ **Inventory/index file formats analyzed**
   - Pydoctor: `searchindex.json` (Lunr.js format) with qualified names
   - Rustdoc: "All Items" HTML page, per-module `sidebar-items.js` files

4. ✅ **HTML structure patterns documented**
   - Content containers, navigation, API elements, code blocks
   - Section hierarchy and heading patterns
   - Both generators fully analyzed

5. ✅ **Sample files downloaded**
   - Pydoctor: HTML pages, search indexes, JavaScript files
   - Rustdoc: HTML pages, sidebar items, crates list
   - All stored in `.auxiliary/scribbles/{pydoctor,rustdoc}-samples/`

6. ✅ **Analysis scripts created**
   - Initial structure analysis: `.auxiliary/scripts/analyze_pydoctor_rustdoc.py`
   - Download scripts: `.auxiliary/scripts/{pydoctor,rustdoc}-analysis/download_samples.sh`

## Ready for Implementation

The following can be implemented directly from the analysis document:

### Pydoctor Support

**Detection:**
- Check for `<meta name="generator" content="pydoctor">`
- Check for `apidocs.css`, `pydoctor.js`
- Check for Bootstrap navbar classes
- Check for `.docstring` elements

**Inventory Extraction:**
- Primary: Parse `searchindex.json` (Lunr.js format)
  - Extract qualified names from field vectors
  - Map to module/class/function hierarchy
- Fallback: Parse `moduleIndex.html`, `classIndex.html`, `nameIndex.html`
- Optional: Check for Sphinx-compatible `objects.inv` (if generated)

**Content Extraction:**
- Main content: Body content (no specific wrapper)
- Docstrings: `.docstring` divs
- Code blocks: `<pre>` elements (check for `.constant-value`, etc.)
- Signatures: Inline `<code>` in headers
- Navigation cleanup: Remove `.navbar`, `.sidebar`

### Rustdoc Support

**Detection:**
- Check for `<meta name="generator" content="rustdoc">`
- Check for `<rustdoc-topbar>`, `<rustdoc-toolbar>` custom elements
- Check for `data-rustdoc-version` attribute
- Check for `rustdoc-*.css` files

**Inventory Extraction:**
- **Recommended:** Parse "All Items" page (`/{crate}/all.html`)
  - Complete listing with type annotations
  - Links to all items
  - Organized by item type
- **Alternative 1:** Crawl `sidebar-items{version}.js` files
  - Navigate module hierarchy
  - Collect items by type (struct, enum, trait, fn, macro, etc.)
- **Alternative 2:** Parse HTML structure directly
  - Very consistent semantic markup
  - Item declarations with full type signatures

**Content Extraction:**
- Main content: `<main>` > `section#main-content`
- Documentation: `.docblock` elements (can be nested)
- Declarations: `<pre class="rust item-decl">`
- Code examples: `.example-wrap` > `<pre class="rust">`
- Cleanup: Remove `nav.sidebar`, `rustdoc-toolbar`, breadcrumbs
- Preserve: Source links (`.src`), stability indicators (`.since`, `.unstable`)

## No Outstanding Questions

All necessary information for implementation has been gathered:

- ✅ Generator identification mechanisms
- ✅ Inventory/index file formats and locations
- ✅ HTML structure patterns for content extraction
- ✅ Code block identification
- ✅ API documentation element patterns
- ✅ Section and navigation structure
- ✅ Theme handling (both have minimal variation)

## Next Steps for Implementation

1. **Create detection modules:**
   - `sources/librovore/structures/pydoctor/detection.py`
   - `sources/librovore/structures/rustdoc/detection.py`

2. **Create inventory modules:**
   - `sources/librovore/inventories/pydoctor/` (parse searchindex.json or HTML indexes)
   - `sources/librovore/inventories/rustdoc/` (parse all-items page or sidebar files)

3. **Create extraction modules:**
   - `sources/librovore/structures/pydoctor/extraction.py`
   - `sources/librovore/structures/rustdoc/extraction.py`

4. **Register processors:**
   - Add to processor registry in `sources/librovore/structures/__init__.py`

5. **Test with reference sites:**
   - Dulwich, Twisted for Pydoctor
   - Rust std, serde, tokio for Rustdoc

## Additional Analysis Scripts (Optional)

The following scripts could be created following the Sphinx/MkDocs pattern, but are not strictly necessary since we already have comprehensive analysis:

- `extract_code_patterns.py` - Detailed code block pattern analysis
- `extract_api_patterns.py` - API element pattern extraction
- `section_analysis.py` - Section structure analysis
- `comprehensive_summary.py` - Final summary comparing all patterns

These would be useful for documentation and verification, but all necessary information is already captured in:
- `.auxiliary/notes/pydoctor-rustdoc.md`
- `.auxiliary/scribbles/pydoctor-rustdoc-analysis.json`
