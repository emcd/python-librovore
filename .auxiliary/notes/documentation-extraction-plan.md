# Documentation Extraction Implementation Plan

## Overview
Add documentation extraction capabilities to complement the existing inventory filtering system. This allows LLMs to find class/function signatures and their corresponding docstrings from Sphinx documentation sites.

## Key Insights from Analysis

### Sphinx Search Index Structure (from searchindex.js)
- **Document mapping**: `"docnames": ["api", "changelog", ...]` → HTML files (api.html, etc.)
- **Object locations**: `"objects"` section format: `[file_index, object_type, priority, anchor, name]`
- **URL Construction**: `linkUrl = docName + docLinkSuffix + anchor`
  - Example: `api.html#sphinxmcps.exceptions.InventoryFilterInvalidity`

### HTML Structure (from api.html analysis)
- **Main content**: `<article role="main" id="furo-main-content">`
- **Objects**: `<dl class="py exception">` (or function, class, etc.)
- **Signatures**: `<dt class="sig sig-object py" id="anchor">`
- **Descriptions**: `<dd>` tags with docstring content
- **Theme**: Furo theme with predictable CSS selectors

### searchtools.js URL Construction Logic
```javascript
// Normal HTML builders (most common)
requestUrl = contentRoot + docName + docFileSuffix;
linkUrl = docName + docLinkSuffix;
linkEl.href = linkUrl + anchor;
```

## Implementation Plan

### Phase 1: Dependencies and Core Infrastructure

#### 1.1 Add Required Dependencies
**Recommended dependencies**:
- `httpx` - Modern async HTTP client (better than requests)
- `beautifulsoup4` - Robust HTML parsing
- `lxml` - Fast XML/HTML parser backend for BeautifulSoup

**Why these choices**:
- `httpx` over `requests`: Better async support, more modern API, built-in timeout handling
- `beautifulsoup4` + `lxml`: BeautifulSoup provides excellent API, lxml provides fast parsing
- No need for `html5lib` - lxml handles HTML parsing well for our needs

#### 1.2 Extend Exception Hierarchy
Add to `sources/sphinxmcps/exceptions.py`:
- `DocumentationInaccessibility` - HTTP fetch failures, 404s, timeouts
- `DocumentationParsingError` - HTML parsing issues, missing expected elements

#### 1.3 Core URL Construction Utilities
Add to `sources/sphinxmcps/functions.py`:
- `_build_documentation_url()` - Convert inventory object URI to documentation URL
- `_extract_base_url()` - Extract base documentation URL from inventory source
- Handle different URL schemes (HTTP/HTTPS, local files with file:// URLs)

### Phase 2: HTML Fetching and Parsing

#### 2.1 HTTP Request Infrastructure
- `_fetch_html_content()` using httpx.AsyncClient
- Proper error handling for timeouts, 404s, network issues
- User-agent headers to identify as documentation extraction tool
- Configurable timeouts (default: 30s)

#### 2.2 HTML Parsing and Content Extraction
- `_parse_documentation_html()` using BeautifulSoup + lxml
- Extract specific sections:
  - Function/class signatures from `<dt class="sig">` elements
  - Docstrings from following `<dd>` elements
  - Parameter descriptions from `<dl class="field-list">`
  - Examples from `<div class="highlight">` code blocks
- Convert HTML to clean Markdown for token efficiency

### Phase 3: MCP Tools Implementation

#### 3.1 `extract_documentation` Tool
**Purpose**: Extract full documentation for specific objects
**Parameters**:
```python
source: SourceArgument  # Reuse existing type
object_name: str  # e.g., "mymodule.MyClass.method"
include_sections: Absential[list[str]] = absent  # signature, description, parameters, examples
output_format: Literal["markdown", "text"] = "markdown"
```

**Implementation Flow**:
1. Use existing inventory filtering to find the object
2. Extract base URL from inventory source
3. Construct documentation URL from object's URI and anchor
4. Fetch HTML content with httpx
5. Parse with BeautifulSoup to extract relevant sections
6. Convert to Markdown and return structured result

#### 3.2 `search_documentation` Tool
**Purpose**: Search across documentation content with relevance ranking
**Parameters**:
```python
source: SourceArgument
query: str  # Search terms
match_mode: MatchMode = MatchMode.EXACT  # Reuse existing enum
max_results: int = 10
include_snippets: bool = True
# Reuse existing filters: domain, role, priority, term
```

**Implementation Flow**:
1. Filter inventory objects using existing filtering system
2. For each matching object, fetch documentation content
3. Perform full-text search with relevance scoring
4. Return ranked results with content snippets

### Phase 4: Function Architecture

#### 4.1 New Type Aliases (following existing patterns)
```python
DocumentationFormat: TypeAlias = Literal["markdown", "text"]
SectionFilter: TypeAlias = Annotated[
    Absential[list[str]], 
    Doc("Sections to include (signature, description, parameters, examples)")
]
DocumentationResult: TypeAlias = dict[str, Any]  # Structured result
SearchResult: TypeAlias = dict[str, Any]  # Search result with metadata
```

#### 4.2 Core Functions (in functions.py)
```python
async def extract_object_documentation(...) -> DocumentationResult
async def search_documentation_content(...) -> list[SearchResult]
async def _fetch_html_content(...) -> str
def _parse_documentation_html(...) -> dict[str, str]
def _build_documentation_url(...) -> str
def _extract_base_url(...) -> str
def _html_to_markdown(...) -> str
```

#### 4.3 Server Integration (in server.py)
- Add tools using existing `@mcp.tool()` decorator pattern
- Use Pydantic Field annotations for parameter documentation
- Handle async operations properly within MCP framework
- Follow existing error handling patterns with try/catch blocks

### Phase 5: Testing Strategy

#### 5.1 Unit Tests (test_200_functions.py)
- Test URL construction with various inventory sources
- Test HTML parsing with fixtures for different documentation formats
- Test error handling for network failures and parsing errors
- Mock httpx requests for consistent testing

#### 5.2 Integration Tests (test_500_integration.py)
- Test MCP tool functionality end-to-end
- Test with real documentation sites (using cached responses)
- Test async functionality within MCP protocol

#### 5.3 Test Fixtures
- HTML content fixtures for different Sphinx themes
- Mock inventory data that corresponds to HTML fixtures
- Network error simulation for robustness testing

#### 5.4 Coverage Requirements
- Maintain 85%+ test coverage as per existing standards
- Focus on error paths and edge cases

### Phase 6: Advanced Features (Future)

#### 6.1 Content Relationship Mapping
- Track relationships between objects (parent classes, related functions)
- Enable "see also" functionality in documentation extraction

#### 6.2 Caching Layer
- Simple file-based caching for fetched documentation content
- Store in `.auxiliary/caches/documentation/` following existing patterns
- Configurable TTL (default: 1 hour for development, 24 hours for production)

#### 6.3 Multi-format Support
- Support for different Sphinx themes (not just Furo)
- Adaptive parsing based on detected documentation structure
- ReadTheDocs, GitHub Pages, custom themes

## Implementation Notes

### Design Principles (per CLAUDE.md)
- Module-level functions, not class methods
- Functions ≤ 30 lines, modules ≤ 600 lines
- Dependency injection with sensible defaults
- Prefer immutability

### Error Handling
- Follow existing patterns in exceptions.py
- Provide specific error messages with context
- Handle network timeouts gracefully
- Fail fast on malformed HTML

### Performance Considerations
- Use httpx.AsyncClient for connection pooling
- Implement reasonable timeouts (30s default)
- Add rate limiting hints for production use
- Cache parsed content when possible

### Security
- Validate URLs before fetching
- Sanitize HTML content appropriately
- Avoid executing any JavaScript from fetched pages
- Use safe HTML parsing with BeautifulSoup

## Current Status
- [x] Analysis of search index structure complete
- [x] HTML structure analysis complete  
- [x] Plan documented
- [x] Dependencies added (httpx, beautifulsoup4, lxml)
- [x] Exception hierarchy extended (DocumentationContentMissing, DocumentationInaccessibility, DocumentationParseFailure)
- [x] URL construction utilities implemented (_build_documentation_url, _extract_base_url)
- [x] HTTP fetching infrastructure implemented (_fetch_html_content with file:// and http/https support)
- [x] HTML parsing functions implemented (_parse_documentation_html, _html_to_markdown)
- [x] MCP tools implemented (extract_documentation with inventory integration)
- [x] Local filesystem support added (file:// URLs, proper path handling)
- [x] BeautifulSoup type stubs created for clean type checking
- [ ] Search functionality implemented (search_documentation tool)
- [ ] Test coverage added
- [ ] Content formatting improvements (signature cleanup, code examples)

## Implementation Achievements

### Core Infrastructure ✅
- **Dependencies**: All required packages (httpx, beautifulsoup4, lxml) integrated
- **Exception System**: Custom exceptions for TRY003 compliance, proper error context
- **URL Construction**: Handles $ placeholder replacement, supports file:// and http/https schemes
- **File System Support**: Local Sphinx documentation works seamlessly

### HTML Processing ✅
- **Multi-format Parsing**: Handles both section elements (modules) and dt/dd pairs (functions/classes)
- **Content Extraction**: Signatures, descriptions, and proper anchor resolution
- **Markdown Conversion**: HTML to markdown with tag cleanup and formatting
- **BeautifulSoup Integration**: Clean type checking with custom minimal type stubs

### MCP Integration ✅
- **extract_documentation Tool**: Fully functional with inventory integration
- **Parameter Validation**: Proper format validation (markdown/text)
- **Error Handling**: Comprehensive error reporting with context
- **Async Support**: Proper async/await throughout the pipeline

## Next Steps
1. Implement search_documentation MCP tool for content search
2. Add comprehensive test coverage for new functionality
3. Improve content formatting (signature cleanup, code examples)
4. Add caching layer for performance
5. Support additional Sphinx themes beyond Furo

This implementation successfully provides documentation extraction capabilities that complement the existing inventory filtering system.