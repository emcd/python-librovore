# Small UX Improvements for Alpha Release

## CLI Structure Changes
- [x] Remove `use` subcommand and hoist subcommands up one level
- [x] Use `tyro.conf.Positional` for the `source` argument
- [x] Add `--extra-functions` argument to `serve` subcommand (controls `detect` and `survey_processors` exposure)
- [x] Rename `source` argument to `location`
- [x] Rename `query` argument to `term`
- [x] Add option for non-JSON output from CLI subcommands
- [x] Convert `--term` to positional argument (positioned after location)
- [x] Strip `index.html` from locations before passing to processors
- [ ] Add `--no-cache` or `--cache-bust` option to bypass HTTP caching

## Content Extraction Quality Issues
- [x] Fix MkDocs extraction picking up admonition titles instead of content
- [x] Improve description extraction to capture actual descriptive text
- [x] Better handling of Material theme admonitions and structured content
- [ ] Test extraction quality across different MkDocs themes

## Additional UX Issues
- [ ] Evaluate error messages and make them more user-friendly
- [ ] Improve CLI help text and examples
- [ ] Add validation for source URLs before processing

## Query Content Display Improvements
- [x] Add `--lines-max` argument to `query-content` (default: 40) for content length control
- [x] Remove redundant "Summary/Preview" field - users can use small `--lines-max` for previews
- [x] Add visual separators between results: `🔍 ── Result N ──────────────────────────── 🔍` with triple blank lines
- [x] Fix blank line preservation in markdownify pipeline for proper paragraph structure
- [ ] Consider future `--compact` flag for condensed display mode

## Processor Detection and Robustness Issues
- [x] Improve MkDocs detection to check HTML meta tags (`mkdocs-material`, `mkdocs` generator) for better hybrid site support

## Ideas for Future
- Look for `llms.txt`? Separate processor or builtin to other processors?
