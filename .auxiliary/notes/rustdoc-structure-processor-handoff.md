# Rustdoc Structure Processor - Handoff Notes

## Status: Ready for Implementation

This document provides handoff notes for implementing the Rustdoc structure processor, which extracts documentation content from Rustdoc-generated HTML pages.

## What Was Completed

✅ **Rustdoc Inventory Processor** (committed on `claude/add-rustdoc-processor-01A4B5jLvPKeKR8M5yLHjKSj`)
- Detection via HTML markers
- Inventory extraction from "All Items" page
- Item type mapping and filtering
- Tested successfully with Rust std, serde, and tokio

## What Needs to Be Done

🔲 **Rustdoc Structure Processor** (this session)
- Content extraction from individual Rustdoc HTML pages
- Conversion to Markdown format
- Support for various Rustdoc content types
- Registration and integration

## Key Differences: Inventory vs Structure Processors

### Inventory Processor
- **Purpose**: Builds index of what exists (like a table of contents)
- **Input**: Index files or "All Items" pages
- **Output**: List of `InventoryObject` instances with metadata
- **Focus**: Discovery and cataloging

### Structure Processor
- **Purpose**: Extracts actual documentation content
- **Input**: Individual HTML pages for specific items
- **Output**: `ContentDocument` instances with formatted text
- **Focus**: Content extraction and conversion

## Architecture Overview

### Directory Structure
```
sources/librovore/structures/rustdoc/
├── __init__.py          # Package with register() function
├── __.py                # Internal imports rollup
├── detection.py         # Rustdoc site detection (reuse inventory detection)
├── main.py              # RustdocStructureProcessor class
├── extraction.py        # Content extraction logic
├── conversion.py        # HTML to Markdown conversion
└── converters.py        # Specific converter functions (optional)
```

## Reference Implementations

### Primary References
1. **Sphinx Structure Processor**: `sources/librovore/structures/sphinx/`
   - `detection.py` - Detection patterns
   - `extraction.py` - Content extraction with BeautifulSoup
   - `conversion.py` - HTML to Markdown via markdownify
   - `main.py` - Processor class with capabilities

2. **MkDocs Structure Processor**: `sources/librovore/structures/mkdocs/`
   - Similar patterns to Sphinx
   - Good reference for alternative approaches

### Key Patterns to Follow
- Inherit from `StructureDetection` base class
- Implement `extract_contents()` method
- Use `parse_documentation_html()` for parsing
- Leverage BeautifulSoup for DOM manipulation
- Use `markdownify` library for HTML→Markdown conversion

## Rustdoc Content Structure

Based on analysis in `.auxiliary/notes/pydoctor-rustdoc.md`:

### Main Content Container
```html
<main>
  <div class="width-limiter">
    <section id="main-content" class="content">
      <!-- Documentation content here -->
    </section>
  </div>
</main>
```

### Key Elements to Extract

1. **Item Declaration** (type signature):
   ```html
   <pre class="rust item-decl">
     pub struct Vec&lt;T&gt; { /* fields omitted */ }
   </pre>
   ```

2. **Documentation Blocks**:
   ```html
   <div class="docblock">
     <p>A contiguous growable array type...</p>
   </div>
   ```

3. **Code Examples**:
   ```html
   <div class="example-wrap">
     <pre class="rust rust-example-rendered">
       let mut v = Vec::new();
     </pre>
   </div>
   ```

4. **Method Sections**:
   - Organized by trait implementation
   - Nested `<details>` elements for collapsible sections

### Elements to Remove/Clean Up
- `<nav class="sidebar">` - Sidebar navigation
- `<rustdoc-toolbar>` - Toolbar elements
- `<rustdoc-topbar>` - Top navigation
- `.sidebar-resizer` - UI elements
- Breadcrumbs (keep or remove based on preference)
- Source links (`.src` anchors)

## Implementation Guidance

### 1. Detection Module (`detection.py`)

Since Rustdoc detection is already implemented in the inventory processor, you have two options:

**Option A**: Share detection logic between inventory and structure
- Move common detection functions to a shared utility module
- Both processors import from the shared module

**Option B**: Duplicate detection logic (simpler, follows existing pattern)
- Copy detection patterns from inventory processor
- Structure processor has its own detection class

**Recommendation**: Option B for consistency with Sphinx/MkDocs pattern

### 2. Main Processor (`main.py`)

```python
class RustdocStructureProcessor( __.Processor ):
    ''' Processes Rustdoc documentation structure. '''

    name: str = 'rustdoc'

    @property
    def capabilities( self ) -> __.ProcessorCapabilities:
        # Define supported filters and features
        pass

    async def detect( self, auxdata, source ) -> __.StructureDetection:
        # Detect Rustdoc site
        pass
```

### 3. Extraction Module (`extraction.py`)

Key functions to implement:

```python
async def extract_contents(
    auxdata: __.ApplicationGlobals,
    source: str,
    objects: __.cabc.Sequence[ __.InventoryObject ], /, *,
    theme: __.Absential[ str ] = __.absent,
) -> list[ __.ContentDocument ]:
    ''' Extracts documentation content for specified objects. '''
    # Main entry point for content extraction

def parse_documentation_html(
    content: str, element_id: str, url: str, *,
    theme: __.Absential[ str ] = __.absent
) -> __.cabc.Mapping[ str, str ]:
    ''' Parses HTML content to extract documentation sections. '''
    # Parse HTML and extract relevant content
```

Content extraction strategy:
1. Fetch HTML page from `InventoryObject.uri`
2. Parse with BeautifulSoup
3. Find `<main>` or `section#main-content`
4. Extract item declaration (`.item-decl`)
5. Extract documentation blocks (`.docblock`)
6. Extract code examples (`.example-wrap`)
7. Clean up unwanted elements
8. Convert to Markdown

### 4. Conversion Module (`conversion.py`)

Use `markdownify` library for HTML→Markdown conversion:

```python
from markdownify import markdownify as _md

def convert_to_markdown( html: str ) -> str:
    ''' Converts Rustdoc HTML to Markdown. '''
    return _md(
        html,
        heading_style = 'ATX',
        code_language = 'rust',  # Default code blocks to Rust
        strip = [ 'nav', 'aside', 'header' ]
    )
```

Special handling for Rustdoc:
- Preserve code language from `.rust`, `.toml`, etc. classes
- Handle nested `.docblock` elements
- Keep example structure with proper formatting
- Preserve trait implementation sections

### 5. Capabilities Definition

Based on comprehensive Rustdoc structure analysis:

```python
supported_inventory_types = frozenset( { 'rustdoc' } )

content_extraction_features = frozenset( {
    ContentExtractionFeatures.Signatures,      # Item declarations
    ContentExtractionFeatures.Descriptions,     # Docblock content
    ContentExtractionFeatures.CodeExamples,     # Example code blocks
    ContentExtractionFeatures.CrossReferences,  # Links to other items
} )

confidence_by_inventory_type = __.immut.Dictionary( {
    'rustdoc': 0.95  # Very high confidence - Rustdoc structure is consistent
} )
```

## Configuration

Add to `data/configuration/general.toml`:

```toml
[[structure-extensions]]
name = "rustdoc"
enabled = true
```

## Testing Strategy

### Manual Testing
Test with these commands:

```bash
# Test detection
hatch run librovore detect --genus structure https://doc.rust-lang.org/std/

# Test content extraction
hatch run librovore query-content https://doc.rust-lang.org/std/ Vec

# Test with other crates
hatch run librovore query-content https://docs.rs/serde/latest/serde/ Serialize
hatch run librovore query-content https://docs.rs/tokio/latest/tokio/ spawn
```

### Test Cases
1. **Structs**: Extract type signature and fields documentation
2. **Enums**: Extract variants and their documentation
3. **Traits**: Extract trait definition and methods
4. **Functions**: Extract signature and documentation
5. **Macros**: Extract macro syntax and examples
6. **Modules**: Extract module-level documentation

### Edge Cases to Handle
- Items with no documentation
- Items with extensive code examples
- Nested trait implementations
- Generic type parameters in signatures
- Lifetime parameters

## Code Style Requirements

Follow the same patterns as the inventory processor:

- ✅ No `__all__` in modules
- ✅ Wide parameter types, narrow return types
- ✅ Immutability preferences (tuple, frozenset, immut.Dictionary)
- ✅ Comprehensive type annotations
- ✅ Narrative mood docstrings with triple single-quotes
- ✅ Spacing around delimiters
- ✅ Exception handling with proper chaining
- ✅ Module organization: imports → type aliases → private constants → public classes → helpers

## Quality Gates

Before committing:

1. ✅ `hatch --env develop run linters` - All linters pass
2. ✅ `hatch --env develop run testers` - All tests pass
3. ✅ Manual testing with Rust std, serde, tokio
4. ✅ Code follows project style guidelines

## Known Considerations

### Rustdoc-Specific Features
- **Versioned resources**: Files like `main-1.84.0.js` include version numbers
- **Custom elements**: `<rustdoc-*>` elements need special handling
- **Semantic markup**: Very consistent structure makes extraction reliable
- **Code highlighting**: Pre-highlighted code blocks with `.rust` class
- **Trait impls**: Complex nested structure for trait implementations

### Potential Challenges
1. **Nested documentation**: `.docblock` elements can be nested
2. **Trait implementations**: Multiple implementation blocks per page
3. **Macro documentation**: Special syntax highlighting
4. **Generic parameters**: Complex type signatures with lifetimes
5. **Source links**: Need to decide whether to preserve or remove

## Success Criteria

A successful implementation should:

1. ✅ Detect Rustdoc sites with high confidence (≥0.90)
2. ✅ Extract clean Markdown from Rustdoc HTML pages
3. ✅ Preserve code examples with proper language tags
4. ✅ Handle all Rustdoc item types (struct, enum, trait, fn, macro, mod)
5. ✅ Pass all quality gates (linters, type checks, tests)
6. ✅ Work with Rust std library, docs.rs crates, and custom Rustdoc sites

## Additional Resources

- **Analysis Document**: `.auxiliary/notes/pydoctor-rustdoc.md`
- **Existing Processors**: `sources/librovore/structures/{sphinx,mkdocs}/`
- **Interfaces**: `sources/librovore/interfaces.py` - `StructureProcessor` protocol
- **Base Classes**: `sources/librovore/processors.py` - `StructureDetection` class

## Questions to Consider

1. Should we preserve source links to Rust source code?
2. How to handle stability indicators (`<span class="since">`, `<span class="unstable">`)?
3. Should trait implementation sections be expanded or kept collapsible in Markdown?
4. How much of the type signature detail to preserve?
5. Should we extract and include navigation context (breadcrumbs)?

---

Good luck with the implementation! The foundation from the inventory processor will make this much smoother.
