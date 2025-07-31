# The Great Transformation: Sphinx → Librovore 🐲📚

*Documenting the metamorphosis of our humble sphinx-mcp-server into the mighty
Librovore - the all-consuming documentation wyrm.*

## Overview

We're renaming the project from `sphinx-mcp-server` to `librovore` to reflect
its expanding scope beyond just Sphinx documentation. The name "librovore"
(book-devourer) better represents our vision of supporting multiple
documentation formats.

## Systematic Approach

### Phase 1: Manual Structural Renames

**Core Package Structure:**
- [x] Rename `sources/sphinxmcps/` → `sources/librovore/`
- [x] Rename `tests/test_000_sphinxmcps/` → `tests/test_000_librovore/`
- [x] Update absolute imports in test suite (`import sphinxmcps` → `import librovore`)

**Project Configuration:**
- [x] Update `pyproject.toml`:
  - [x] `name = "sphinx-mcp-server"` → `name = "librovore"`
  - [x] Script entrypoint: `sphinxmcps = "sphinxmcps.cli:execute"` → `librovore = "librovore.cli:execute"`
  - [x] Any other package name references

### Phase 2: Content Updates

**Documentation:**
- [x] Update `documentation/api.rst` autodoc references
- [x] Update `.mcp.json` MCP server reference

**Code Content (via global search):**
- [x] CLI help text and descriptions mentioning "Sphinx MCP Server"
- [x] Module docstrings with package descriptions
- [x] Log messages mentioning old name
- [x] Error messages referencing "sphinxmcps"
- [x] Comments mentioning old project name
- [x] Any hardcoded string literals

**Extension Manager Check:**
- [x] Verify no dynamic imports using old package name

### Phase 3: Copier Template Update

**Preparation:**
- [x] Ensure all manual renames are complete first

**Execution:**
- [ ] Run `copier update --answers-file .auxiliary/configuration/copier-answers.yaml`
- [ ] Resolve any merge conflicts (especially in `pyproject.toml`)
- [ ] Review generated GitHub Actions workflows

### Phase 4: Repository Operations

**Upstream Repository:**
- [ ] Rename Git repository (currently in Dropbox)
- [ ] Update `origin` remote to point at renamed repository
- [ ] Rename local directory where clone lives

### Phase 5: Cache Invalidation & Environment Cleanup

**Clean Slate:**
- [ ] Clear `.auxiliary/caches/` directory
- [ ] Clear pytest caches
- [x] Run `hatch env prune` to clean environments
- [x] Reinstall in development mode

### Phase 6: Validation

**Functionality Tests:**
- [x] Run full test suite (`hatch --env develop run testers`)
- [x] Run linters (`hatch --env develop run linters`)
- [x] Test CLI functionality with new command name
- [ ] Test MCP server functionality
- [ ] Verify documentation generation

## Key Insights

- **Interface Stability**: "Interfaces are never stable until at least three implementations" - we'll refine our processor interface after adding MkDocs support
- **Future Vision**: The rename sets us up perfectly for `llms.txt` processor support later
- **Branding**: 🐲📚 "Book Wyrm" - the legendary documentation devourer

## Risk Mitigation

- Complete manual renames before Copier update to avoid template conflicts
- Systematic validation at each phase
- Git commit after each major phase for easy rollback
- Test both MCP server and CLI functionality thoroughly

## Success Criteria

- [ ] All tests pass with new package name
- [ ] CLI command `librovore` works correctly
- [ ] MCP server registers and functions properly
- [ ] No lingering references to `sphinxmcps` in codebase
- [ ] Documentation builds without errors
- [ ] Ready for MkDocs processor development

---

*"From humble Sphinx to mighty Wyrm - devouring documentation across all formats!"* 🐲
