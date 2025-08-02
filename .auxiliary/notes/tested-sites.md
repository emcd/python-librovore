# Tested Documentation Sites

Reference list of sites tested with both Sphinx and MkDocs processors for future validation.

## ✅ Successfully Tested Sites

### MkDocs Sites (with mkdocstrings)

### **FastAPI** - https://fastapi.tiangolo.com/
- **Theme**: Material for MkDocs
- **Inventory**: 1349 objects via mkdocstrings
- **Test Query**: `APIRouter` → Clean signatures and descriptions
- **HTML-to-Markdown**: Excellent conversion quality

### **Pydantic** - https://docs.pydantic.dev/latest/
- **Theme**: Material for MkDocs  
- **Inventory**: 1066 objects via mkdocstrings
- **Test Query**: `BaseModel` → Proper content extraction
- **HTML-to-Markdown**: High-quality markdown output

### **mkdocstrings** - https://mkdocstrings.github.io/
- **Theme**: Material for MkDocs
- **Inventory**: 539 objects (self-documenting)
- **Test Query**: `AutoDocProcessor` → Meta-documentation extraction
- **HTML-to-Markdown**: Clean conversion of technical content

### Sphinx Sites

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

### **HTTPX** - https://www.python-httpx.org/
- **Status**: Pure MkDocs without mkdocstrings - no inventory available
- **Reason**: Correctly rejected (no objects.inv file)
- **Future**: Could support with pure content parsing (no API objects)

## ⚠️ Sites with Historical Issues (Now Resolved)

### **sphobjinv** - https://sphobjinv.readthedocs.io/en/stable/
- **Previous Issue**: Explore function failed with errors
- **Status**: Likely resolved with performance improvements

## Testing Notes

### Sphinx Processor
- All major themes (Furo, pydoctheme, ReadTheDocs, custom) work correctly
- DSL-driven content extraction handles theme variations automatically
- Single-pass HTML-to-Markdown conversion provides clean output
- Proper spacing preservation in text extraction

### MkDocs Processor  
- Material for MkDocs theme fully supported
- mkdocstrings integration provides rich API documentation
- Enhanced HTML-to-Markdown with language-aware code blocks
- Admonition processing converts to clean text format
- Navigation cleanup removes Material theme UI elements

### General
- robots.txt 404 handling works correctly for GitHub Pages sites
- Dual processor architecture automatically selects appropriate handler
- Consistent markdown output across both documentation systems
- Language detection in code blocks ready for future Pygments integration
