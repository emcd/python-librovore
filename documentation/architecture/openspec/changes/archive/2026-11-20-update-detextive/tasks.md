## 1. Dependencies

- [x] 1.1 Pin `detextive~=3.1` in `pyproject.toml` (no detector extras).
- [x] 1.2 Refresh the hatch develop environment and confirm imports resolve.

## 2. Single-Decode Flow

- [x] 2.1 Add a shared decode helper in `cacheproxy.py`: single `decode()`
  call, catch-and-retry with `trial_codecs=(charset_default,)`, mapped
  scheme errors. Unknown header charsets are pre-gated via
  `codecs.lookup` and treated as absent; configuration codec errors
  propagate.
- [x] 2.2 Rewire the file-scheme branch to the helper with
  `location=path`; delete `detect_mimetype_and_charset` usage.
- [x] 2.3 Rewire cached-HTTP and fresh-HTTP paths to the helper with
  `http_content_type=` header and `location=url`; the returned string is
  used directly, never re-decoded.
- [x] 2.4 Delete `_extract_charset_from_headers`,
  `_extract_mimetype_from_headers`, `_detect_charset_with_fallback`, and
  `_detect_mimetype_with_fallback` once subsumed; use
  `parse_http_content_type` only where a raw header value is still needed.
- [x] 2.5 Retire all old detection entry points except
  `is_textual_mimetype`, which is retained for the explicit header-MIME
  gate; `detect_charset`/`detect_mimetype` take no header guidance.

## 3. Tests

- [x] 3.1 Delete header-parser unit tests (`test_030`–`test_037`) with the
  parser.
- [x] 3.2 Replace the `fs_chardet` workaround with sanctioned harness-only
  `Behaviors(charset_detectors_order=(), trial_decode=Never,
  trial_codecs=('utf-8', 'utf-8-sig'))` in pyfakefs tests (verified cold:
  zero detector involvement; explicit trials keep results independent of
  locale defaults).
- [x] 3.3 Add a real-filesystem smoke subset (no pyfakefs) exercising
  production-default detector order: utf-8 file, alternate-charset file,
  binary file rejection.
- [x] 3.4 Add boundary tests: unknown header charset and known non-text
  codec headers (`base64_codec`, `rot_13`) stripped with MIME retained,
  non-textual MIME rejected without decoding, empty non-textual HTTP body
  rejected on cache-hit and cache-miss paths, empty textual body still
  valid, default-charset fallback engaged; assert decode-to-text only,
  never labels.
- [x] 3.5 Confirm no test asserts on, maps, or imports detector artifacts;
  the disabled-detection harness configuration is the only permitted
  detector reference.

## 4. Validation

- [x] 4.1 Run `hatch --env develop run testers` green on a fresh environment.
- [x] 4.2 Run linters (`ruff`, `pyright`) and confirm the manifest carries no
  direct detector-package dependencies.
