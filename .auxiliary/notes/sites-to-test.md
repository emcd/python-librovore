# Documentation Sites Test List

Definitive list of sites for testing both Sphinx and MkDocs processors.

## Sites Expected to Work

### MkDocs Sites (with mkdocstrings)

**FastAPI** - https://fastapi.tiangolo.com/
- Test queries: `APIRouter`, content search for `APIRouter`
- Expected: 1349+ objects, comprehensive API documentation

**Pydantic** - https://docs.pydantic.dev/latest/
- Test queries: `BaseModel`, content search for validation
- Expected: 1066+ objects, model documentation

**mkdocstrings** - https://mkdocstrings.github.io/
- Test queries: `AutoDocProcessor`, content search for handlers
- Expected: 539+ objects, meta-documentation

### Sphinx Sites

**pytest** - https://docs.pytest.org/en/latest/
- Test queries: `fixture`, content search for `pytest.fixture`
- Expected: 1245+ objects, comprehensive testing framework docs

**Python docs** - https://docs.python.org/3/
- Test queries: `print`, `asyncio`, content search for built-ins
- Expected: 17,080+ objects, standard library documentation

**Requests** - https://requests.readthedocs.io/en/latest/
- Test queries: `requests.get`, content search for `GET request`
- Expected: 221+ objects, HTTP library documentation
- Note: Requires URL pattern extension (readthedocs.io → readthedocs.io/en/latest/)

**python-appcore** - https://emcd.github.io/python-appcore/stable/sphinx-html/
- Test queries: `appcore`, content search for `appcore.prepare`
- Expected: 88+ objects, application framework docs

**tyro** - https://brentyi.github.io/tyro/
- Test queries: content search for `tyro.cli`
- Expected: Argument parsing library documentation

**NumPy** - https://numpy.org/doc/stable/
- Test queries: `numpy.array`, content search for array operations
- Expected: 8,449+ objects, scientific computing docs

**pandas** - https://pandas.pydata.org/docs/
- Test queries: `DataFrame`, content search for data manipulation
- Expected: 15,428+ objects, data analysis documentation

**Django** - https://docs.djangoproject.com/en/5.2/
- Test queries: `Model`, content search for ORM
- Expected: 7,695+ objects, web framework documentation
- Note: Use versioned URL, main URL has inventory issues

**Flask** - https://flask.palletsprojects.com/
- Test queries: `Flask`, content search for routing
- Expected: 628+ objects, micro-framework documentation

**Panel** - https://panel.holoviz.org/
- Test queries: `Panel`, content search for `ReactiveHTML`
- Expected: 2,392+ objects, dashboarding framework
- Note: Original librovore motivation site

**sphobjinv** - https://sphobjinv.readthedocs.io/en/stable/
- Test queries: `sphobjinv`, content search for inventory tools
- Expected: 220+ objects, Sphinx inventory tools

## Sites Previously Failing (Now Working)

**HTTPX** - https://www.python-httpx.org/
- Status: ✅ **NOW WORKING** - Pure MkDocs via inventory processor 
- MkDocs processor confidence: 0.8
- Inventory objects: 184+ matches for typical searches
- Validation: Full inventory and content queries working

## Problematic Sites for Pattern Extension Testing

**docs.pydantic.dev** - https://docs.pydantic.dev/
- Purpose: Test URL pattern extension (redirects to /latest/)
- Expected: Should resolve automatically and work

**starlette.readthedocs.io** - https://starlette.readthedocs.io/
- Purpose: Test ReadTheDocs pattern extension
- Expected: Should extend to /en/latest/ and work

## Test Parameters

### Inventory Queries
- Search for main library objects (class names, function names)
- Verify object counts match expected ranges
- Test fuzzy matching with partial terms

### Content Queries  
- Search for specific topics and concepts
- Verify HTML-to-Markdown conversion quality
- Test parameter documentation extraction

### Error Scenarios
- Verify appropriate error messages for unsupported sites
- Test URL pattern extension behavior
- Validate redirects cache functionality

## Testing Checklist

- [x] All expected-to-work sites return valid inventories
- [x] Content queries return well-formatted markdown
- [x] Previously failing sites (HTTPX) now work with MkDocs processor
- [x] URL pattern extension works for problematic sites
- [x] Performance remains acceptable across all inventory sizes
- [x] Theme compatibility maintained across different documentation themes
- [x] Precedence system works correctly (Sphinx > MkDocs)
