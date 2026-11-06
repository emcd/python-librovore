## Why

Librovore pins `detextive~=1.0`, whose detection API was renamed in 2.x and whose decode semantics changed in 3.x, while the ecosystem moved on: fresh installs now resolve `chardet` 7.x, whose binary model data files break our pyfakefs-based tests. Porting to `detextive` 3.x restores a supported foundation, lets all character detection go through Detextive (no direct `chardet`/`charset-normalizer`/`python-magic`/`puremagic` dependencies, none of which we declare today and none of which we will add), and lets our tests assert only our own contract instead of detector internals.

## What Changes

- Pin `detextive~=3.1` (allows 3.x minors, blocks 4.0). No detector extras,
  no new direct dependencies on detector packages.
- Replace the six `detextive` 1.0 call sites in `sources/librovore/cacheproxy.py`
  with a single-decode flow per scheme: decode once via `decode()` and reuse
  the result instead of trial-decoding and re-decoding independently.
  - File branch: `decode(content, location=path)`; on
    `{ContentDecodeFailure, ContentDecodeImpossibility, TextInvalidity}`
    retry once with `trial_codecs=(charset_default,)` (preserves the public
    `charset_default` fallback scenario), then raise
    `DocumentationInaccessibility`.
  - HTTP branches (cache hit and fresh fetch alike): first an explicit
    header-MIME gate (non-textual declared MIME raises
    `HttpContentTypeInvalidity` before decoding — required because `decode`
    short-circuits enforcement on empty input), then `decode(content,
    http_content_type=header, location=url)` with the same catch-and-retry,
    mapping final failure to `HttpContentTypeInvalidity`.
  - Header policy: unknown header charsets (failing `codecs.lookup`) and
    known non-text codecs (`codecs.lookup` succeeds but
    `_is_text_encoding` is false, e.g. `base64_codec`, `rot_13`,
    `hex_codec`) are stripped while their MIME is retained for the gate,
    so input-driven garbage can never surface as `LookupError`;
    configuration codec errors still propagate loudly.
  - The old detection entry points (`detect_mimetype_and_charset`,
    `detect_charset`, `detect_mimetype`, `is_textual_content`) are fully
    retired from our code; all detection flows through `decode()`, except
    `is_textual_mimetype`, which is retained solely for the explicit header
    gate. `detect_charset`/`detect_mimetype` do not accept
    `http_content_type` in any case; header guidance flows exclusively
    through `decode()`/`decode_inform()`.
- Delete hand-rolled `_extract_charset_from_headers`,
  `_extract_mimetype_from_headers`, `_detect_charset_with_fallback`, and
  `_detect_mimetype_with_fallback` once the single-decode flow subsumes them;
  parse headers only via Detextive where a raw value is still needed.
- Tests: delete header-parser unit tests with the parser; replace the `fs_chardet` chardet-data workaround with sanctioned harness-only `Behaviors(charset_detectors_order=(), trial_decode=Never, trial_codecs=('utf-8', 'utf-8-sig'))` in pyfakefs tests (demonstrated cold to avoid all detector execution, independent of locale; detection itself is covered by the real-filesystem smoke subset under production defaults); keep decode-to-text assertions, add no label assertions.
- Close port todos `python-librovore:todos/2` on landing.

## Capabilities

### New Capabilities

- `text-decoding`: bytes-to-text retrieval contract for file and HTTP schemes — detection, validation, header guidance, fallback, and error mapping. No existing spec covers this behavior.

### Modified Capabilities

(none — no existing spec requirements change; `caching`, `search`, and other specs keep their current wording)

## Impact

- `sources/librovore/cacheproxy.py` (detection call sites, header helpers, error mapping).
- `tests/test_000_librovore/conftest.py`, `test_110_cacheproxy.py` (fixture and parser-test removal, behavior configuration).
- `pyproject.toml` (`detextive~=3.1`, develop extra for tests).
- Detextive Owner consulted for API mapping; follow-ups as implementation proceeds.
