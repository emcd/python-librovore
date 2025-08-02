# Tested Sphinx Documentation Sites

Reference list of sites tested with the Sphinx MCP processor for future validation.

## ✅ Successfully Tested Sites

### **pytest** - https://docs.pytest.org/en/latest/
- **Theme**: Furo
- **Inventory**: 1245 objects, version 8.5.0.dev64
- **Test Query**: `pytest.fixture` → Full signature and detailed description

### **Python docs** - https://docs.python.org/3/
- **Theme**: pydoctheme
- **Inventory**: Large, comprehensive
- **Test Query**: `print` → Complete signature and description

### **Requests** - https://requests.readthedocs.io/en/latest/
- **Theme**: ReadTheDocs
- **Inventory**: 221 objects, version 2.32.4
- **Test Query**: `requests.get` → Full signature and description

### **python-appcore** - https://emcd.github.io/python-appcore/stable/sphinx-html/
- **Theme**: Custom
- **Inventory**: 88 objects, version 1.4
- **Test Query**: `appcore.prepare` → Comprehensive content extraction

### **tyro** - https://brentyi.github.io/tyro/
- **Theme**: Furo
- **Test Query**: `tyro.cli` → Perfect content extraction with proper spacing

## ❌ Sites That Correctly Failed Detection

**Tested Sites:**
- ✅ **Pydantic** (`docs.pydantic.dev/latest/`) - Has objects.inv, works with
  current Sphinx processor
- ✅ **FastAPI** (`fastapi.tiangolo.com/`) - Has objects.inv, works with
  current Sphinx processor
- ✅ **mkdocstrings** (`mkdocstrings.github.io/`) - Has objects.inv, reference
  implementation
- ❌ **HTTPX** (`python-httpx.org/`) - Pure MkDocs, no inventory (future scope)

### **httpx** - https://www.python-httpx.org/
- Uses MkDocs (correctly rejected)

### **Pydantic** - https://docs.pydantic.dev/
- Uses MkDocs (correctly rejected)

## ⚠️ Sites with Historical Issues (Now Resolved)

### **sphobjinv** - https://sphobjinv.readthedocs.io/en/stable/
- **Previous Issue**: Explore function failed with errors
- **Status**: Likely resolved with performance improvements

## Testing Notes

- All major themes (Furo, pydoctheme, ReadTheDocs, custom) work correctly
- DSL-driven content extraction handles theme variations automatically
- Single-pass HTML-to-Markdown conversion provides clean output
- Proper spacing preservation in text extraction
- robots.txt 404 handling works correctly for GitHub Pages sites
