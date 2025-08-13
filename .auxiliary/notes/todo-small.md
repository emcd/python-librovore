# Small UX Improvements for Alpha Release

## CLI Structure Changes
- [x] Remove `use` subcommand and hoist subcommands up one level
- [x] Use `tyro.conf.Positional` for the `source` argument
- [ ] Add `--extra-functions` argument to `serve` subcommand (controls `detect` and `survey_processors` exposure)
- [ ] Rename `source` argument to `location` 
- [ ] Rename `query` argument to `term`
- [ ] Add option for non-JSON output from CLI subcommands
- [ ] Add `--no-cache` or `--cache-bust` option to bypass HTTP caching

## Content Extraction Quality Issues
- [x] Fix MkDocs extraction picking up admonition titles instead of content
- [x] Improve description extraction to capture actual descriptive text
- [x] Better handling of Material theme admonitions and structured content
- [ ] Test extraction quality across different MkDocs themes

## Additional UX Issues
- [ ] Evaluate error messages and make them more user-friendly
- [ ] Consider adding progress indicators for long-running operations
- [ ] Improve CLI help text and examples
- [ ] Add validation for source URLs before processing

## Ideas for Future
- Look for `llms.txt`? Separate processor or builtin to other processors?
