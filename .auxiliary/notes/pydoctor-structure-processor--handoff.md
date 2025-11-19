# Pydoctor Structure Processor - Session Handoff

## Session Context

**Previous session**: Implemented Pydoctor inventory processor (completed and committed)
**Next session**: Implement Pydoctor structure processor for content extraction

## What Was Completed

✅ Pydoctor **Inventory Processor** (`sources/librovore/inventories/pydoctor/`)
- Detection via `searchindex.json` presence
- Extraction of qualified names from Lunr.js format
- Object type inference (module/class/function)
- Type filtering support
- Successfully tested with local test data
- Committed to branch: `claude/add-pydoctor-inventory-01S3oFrZAL2SGeNbZLbj4tSK`

## What's Next: Structure Processor

The structure processor extracts **content** (documentation text, signatures, descriptions) from Pydoctor HTML pages.

### Implementation Location

Create: `sources/librovore/structures/pydoctor/`

### Reference Implementations

- **Sphinx structure**: `sources/librovore/structures/sphinx/`
  - `detection.py` - Detection patterns
  - `extraction.py` - Content extraction logic
  - `conversion.py` - HTML to text conversion
  - `converters.py` - Specialized converters
  - `main.py` - Main processor class

- **MkDocs structure**: `sources/librovore/structures/mkdocs/`
  - Similar pattern but simpler extraction

### Key Resources from Analysis

From `.auxiliary/notes/pydoctor-rustdoc.md`:

**HTML Structure Patterns** (Pydoctor v24.11.2):
- Generator meta tag: `<meta name="generator" content="pydoctor X.Y.Z">`
- Content container: `div.page`
- Module/class signatures: `code.moduleName`, `code.classQualifiedName`
- Docstrings: `div.docstring`
- Function signatures: `div.functionHeader code`
- Navigation: `nav.navbar.mainnavbar`

**Content Extraction Strategy**:
1. Parse HTML for object being requested
2. Extract signature from appropriate container
3. Extract docstring from `div.docstring`
4. Convert HTML docstrings to markdown/text
5. Return as `ContentDocument`

### Architecture Pattern to Follow

```
sources/librovore/structures/pydoctor/
├── __.py                 # Import rollup
├── __init__.py          # Registration function
├── detection.py         # Structure detection (check for pydoctor HTML)
├── extraction.py        # Main extraction logic
├── conversion.py        # HTML → text conversion
├── converters.py        # Specialized converters (optional)
└── main.py             # PydoctorStructureProcessor class
```

### Key Classes to Implement

1. **PydoctorStructureDetection** (extends `StructureDetection`)
   - Detects Pydoctor HTML structure
   - Implements `extract_contents()` method
   - Returns `ContentDocument` tuples

2. **PydoctorStructureProcessor** (extends `Processor`)
   - Provides capabilities for content extraction
   - Implements `detect()` method
   - Specifies content extraction features supported

### Extraction Features to Support

Based on analysis, Pydoctor has clear patterns for:
- ✅ **signatures**: Function/class signatures in `code` elements
- ✅ **descriptions**: Docstrings in `div.docstring`
- ⚠️ **code-examples**: May be in docstrings (need to check)
- ⚠️ **cross-references**: Links in docstrings
- ⚠️ **arguments**: May need custom parsing
- ⚠️ **returns**: May need custom parsing
- ⚠️ **attributes**: Class/module attributes

### URL Pattern for Content Retrieval

From inventory processor, URIs are: `{qname.replace('.', '/')}.html`

Example:
- Inventory object: `twisted.internet.reactor`
- Content URL: `{base_url}/twisted/internet/reactor.html`

### Detection Strategy

**Primary markers**:
1. Check for `<meta name="generator" content="pydoctor">`
2. Check for typical Pydoctor CSS: `apidocs.css`, `readthedocstheme.css`
3. Check for structural elements: `div.page`, `nav.mainnavbar`

**Detection confidence**:
- Meta tag present: 1.0
- CSS + structure: 0.8
- Structure only: 0.5

### HTML Parsing Approach

Use BeautifulSoup (already in dependencies via Sphinx processor):
```python
from bs4 import BeautifulSoup

def extract_signature(soup: BeautifulSoup, qname: str) -> str:
    # Find code.classQualifiedName or code.moduleName
    ...

def extract_docstring(soup: BeautifulSoup) -> str:
    # Find div.docstring
    # Convert HTML to markdown/text
    ...
```

### Content Extraction Flow

```python
async def extract_contents(
    self,
    auxdata: ApplicationGlobals,
    source: str,
    objects: Sequence[InventoryObject],
) -> tuple[ContentDocument, ...]:
    """Extract content for each inventory object."""

    for obj in objects:
        # 1. Construct full URL from obj.uri
        content_url = f"{source}/{obj.uri}"

        # 2. Fetch HTML
        html = await retrieve_url(auxdata.content_cache, content_url)

        # 3. Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # 4. Extract signature + docstring
        signature = extract_signature(soup, obj.name)
        docstring = extract_docstring(soup)

        # 5. Build ContentDocument
        doc = ContentDocument(
            inventory_object=obj,
            content_id=produce_content_id(source, obj.name),
            description=f"{signature}\n\n{docstring}",
            documentation_url=content_url,
        )

        yield doc
```

### Registration

Add to `data/configuration/general.toml`:
```toml
[[structure-extensions]]
name = "pydoctor"
enabled = true
```

### Testing Approach

1. **Local test**: Create minimal Pydoctor HTML file in `.auxiliary/scribbles/`
2. **Real site test**: Use Twisted or Dulwich for integration testing
3. **Verify extraction**: Check signatures and docstrings are extracted correctly

### Known Challenges

1. **HTML variations**: Different Pydoctor versions may have different structure
2. **Docstring formats**: May be restructuredText, Markdown, or Epytext
3. **Complex objects**: Methods, properties, attributes need special handling
4. **Performance**: Large sites like Twisted have 10K+ objects

### Success Criteria

- ✅ Detects Pydoctor structure pages
- ✅ Extracts signatures for classes/functions/modules
- ✅ Extracts docstrings from `div.docstring`
- ✅ Converts HTML to readable text/markdown
- ✅ Returns properly formatted `ContentDocument` objects
- ✅ Works with Twisted/Dulwich reference sites
- ✅ All linters pass
- ✅ Existing tests pass

### Reference Sites for Testing

1. **Twisted**: https://docs.twistedmatrix.com/en/stable/api/
   - Large, comprehensive API (10MB+ searchindex)
   - Pydoctor 24.11.2
   - Has both Sphinx and Pydoctor inventories

2. **Dulwich**: https://www.dulwich.io/api/
   - Smaller, more manageable
   - Good for initial testing

### Sample HTML to Expect

From Twisted analysis:
```html
<div class="page">
  <code class="moduleName">twisted.internet.reactor</code>
  <div class="docstring">
    <p>The reactor module contains the main event loop...</p>
  </div>
</div>
```

For classes:
```html
<code class="classQualifiedName">twisted.internet.defer.Deferred</code>
<div class="functionHeader">
  <code>__init__(self, canceller=None)</code>
</div>
<div class="docstring">
  <p>Initialize a Deferred...</p>
</div>
```

### Dependencies Already Available

From Sphinx/MkDocs processors:
- `beautifulsoup4` - HTML parsing
- `httpx` - Async HTTP client
- Conversion utilities in parent modules

### Suggested Session Flow

1. Review Sphinx structure processor for patterns
2. Review Pydoctor HTML analysis
3. Create package structure files
4. Implement detection logic
5. Implement basic extraction (signatures + docstrings)
6. Test with local HTML samples
7. Test with real sites
8. Add to configuration
9. Run linters and tests
10. Commit and push

## Files to Review Before Starting

1. `.auxiliary/notes/pydoctor-rustdoc.md` - Comprehensive HTML structure analysis
2. `sources/librovore/structures/sphinx/` - Reference implementation pattern
3. `sources/librovore/interfaces.py` - `StructureProcessor` protocol
4. `sources/librovore/processors.py` - `StructureDetection` base class
5. `.auxiliary/instructions/practices-python.rst` - Coding standards

## Questions to Consider

1. How to handle multiple docstring formats (reST, Markdown, Epytext)?
2. Should we extract method/attribute details separately?
3. How to handle inherited documentation?
4. Performance optimization for large inventories?
5. Should we support theme variations?

## Notes

- Pydoctor often generates Sphinx `objects.inv` for compatibility
- Some sites may have both structure processors available
- Structure processor should work independently of inventory source
- Focus on quality over quantity - better to extract fewer things well
