# Design: Detextive 3.x Port

## Context

`cacheproxy.py` is the only module touching Detextive (six call sites). The
1.0 API surface it uses was renamed in 2.x (`detect_mimetype_and_charset`,
`is_textual_content`) and re-semanticed in 3.x (decode-or-error, boolean
`Behaviors`, `http_content_type` honored throughout). Detextive Owner verified
the target mapping against the 3.1 wheel. The stale 2.0 port branch
(`claude/port-detextive-2.0-…`, one commit plus stash on a pre-1.0-era base)
is abandoned; this change ports from current `master` instead of rebasing it.

Constraints: `requires-python >= 3.12` already satisfied by the recent
baseline update; no direct detector-package dependencies may be added;
`pyfakefs`-based tests must pass on fresh resolves.

## Goals / Non-Goals

Goals: all six call sites on 3.x API; header parsing delegated to Detextive;
file-scheme and HTTP text paths share one decode-first shape; tests assert
only Librovore behavior (decode-to-text, caching, error mapping) with no
detector awareness.

Non-goals: no change to cache storage/TTL, CLI, MCP, or result rendering;
no `python-magic` extra (puremagic suffices); no exact-label assertions.

## Decisions

1. **Decode-first gate via `decode()`, not `decode_inform()`.**
   Rationale: the gate needs only a pass/fail answer; `decode_inform()`
   adds mimetype/linesep inference cost for metadata we discard.
   Alternative (decode-then-`is_valid_text`) rejected: double validation
   work and a redundant failure mode.

2. **Catch exactly `{ContentDecodeFailure, ContentDecodeImpossibility,
   TextInvalidity}`** at each gate, mapping to `DocumentationInaccessibility`
   (file scheme) or `HttpContentTypeInvalidity` (HTTP scheme).
   Rationale: per Detextive Owner this set is complete for the decode path
   under default `Behaviors`; catching `Omnierror` would mask programming
   errors such as `BehaviorsInvalidity`. `TextualMimetypeInvalidity` was not
  observed escaping `decode()` in probing (non-textual header MIME surfaces
  as `ContentDecodeImpossibility`); if implementation surfaces it, map it
  identically via fixup rather than broadening the catch set preemptively.

  Flow shape per scheme (verified against 3.1 behavior):

  - File: `text = decode(content, location=path)`. On the catch set above,
    retry once with `trial_codecs=(charset_default,)`; on repeat failure
    raise `DocumentationInaccessibility`. This preserves the public
    `charset_default` fallback scenario: the default is honored as the final
    trial, not as a silent return (`decode` has no `charset_default`
    keyword, and `charset_supplement` is not equivalent).
  - Cached HTTP and fresh HTTP alike: first apply an explicit
    header-MIME gate — parse the Content-Type with Detextive's parser and,
    if it declares a non-textual mimetype, raise `HttpContentTypeInvalidity`
    before decoding. The gate is required because `decode` short-circuits
    enforcement on empty input (verified: empty body plus non-textual header
    MIME returns `''`, while non-empty input raises). Then `text =
    decode(content, http_content_type=header, location=url)` with the same
    catch-and-retry, mapping final failure to `HttpContentTypeInvalidity`.
    The returned string is used directly — never trial-decoded and then
    re-decoded with another charset.
  - `detect_charset`/`detect_mimetype` do NOT accept `http_content_type`
    (TypeError on 3.1); header guidance flows exclusively through
    `decode()`/`decode_inform()`. The old
    `_detect_charset_with_fallback` / `_detect_mimetype_with_fallback`
    helpers are deleted, not converted.

3. **Pass `http_content_type=` into `decode()`; delete our header parser.**
   Rationale: header-guided trial decode inside Detextive supersedes the
   hand-rolled parser, removing `test_030`–`test_037` and a drift surface.
   Raw header values come from `parse_http_content_type` only where a raw
   value is still needed (the pre-gate below).
   Input-driven header policy: an unknown header charset (failing
   `codecs.lookup`) or a known non-text codec (`codecs.lookup` succeeds
   but `_is_text_encoding` is false — e.g. `base64_codec`, `rot_13`,
   `hex_codec`, all of which raise `LookupError: ... is not a text
   encoding` in `decode`) is stripped while its MIME is retained — the
   gate still enforces the MIME and `decode` receives the mimetype-only
   header — so input-driven garbage can never surface as `LookupError`;
   configuration codec errors still propagate loudly, so programming errors
   are not masked. A missing `_is_text_encoding` attribute degrades to
   treating the codec as usable, letting `decode` decide.

4. **Scheme fallback as catch-and-retry with the public default, not
   supplement.**
   `charset_supplement` is a trial hint, never a fallback return; fallback
   semantics are try `decode()`, catch the decode-failure set, retry with
   `trial_codecs=(charset_default,)`, mapping repeat failure to the
   scheme error. With the default `charset_default='utf-8'` this is the
   utf-8-last shape; a caller-supplied default is honored the same way.
   In practice bare `decode()` already trials utf-8 early, so the retry
   path triggers rarely.

5. **Pyfakefs tests run under sanctioned harness-only
   `Behaviors(charset_detectors_order=(), trial_decode=Never,
   trial_codecs=('utf-8', 'utf-8-sig'))`.**
   Rationale: removes the `fs_chardet` chardet-data workaround entirely —
   with an empty detector order and trial decode disabled, decode proceeds
   deterministically with zero detector involvement (verified cold under
   pyfakefs: utf-8 and ascii decode, binary raises `ContentDecodeFailure`,
   empty decodes to `''`), and no test asserts on, maps, or imports
   detector artifacts. Explicit trial codecs (rather than inherited
   defaults) keep results independent of `OsDefault`/`PythonDefault`
   locale slots. This is harness-level backend configuration, explicitly
   permitted; it is not a test of detector behavior. Production keeps
   default detection (chardet first, closest to current behavior).
   Alternative (keep `add_real_file` mapping) rejected per operator direction:
   tests must not know about chardet.
   Correction to earlier drafts, verified on published 3.1 and confirmed
   with Detextive Owner: a normalizer-first ordering does NOT keep chardet
   out, and neither does `charset_detect=False` alone — the decode entry
   path calls detection unconditionally on 3.1 (only the infer entry points
   honor the flag; fixed on Detextive master for 3.2 to honor it in
   decode as well). The empty order plus disabled trial decode is the only
   combination demonstrated cold to avoid all detector execution; it is
   version-independent, working identically before and after the 3.2 fix.
   The suite-wide real-filesystem smoke subset exercises
   production-default Behaviors (chardet active, no pyfakefs) alongside
   the pyfakefs tests, so detection itself remains covered without
   detector-aware unit tests.

6. **Pin `detextive~=3.1`; no detector extras required.**
   Rationale: `~=` tracks 3.x minors while blocking 4.0, so the 3.2 fix
   (honoring `charset_detect` in decode) is admitted automatically; the
   harness mechanism is version-independent either way. No extras are
   needed: pyfakefs tests run detection-free, and the real-filesystem
   smoke subset uses production defaults (chardet ships with detextive).

## Risks / Trade-offs

- [Risk] Heuristic label differences on ambiguous bytes change which charset
  is reported (owner-confirmed inherent drift). → Mitigation: tests assert
  decode-to-expected-text only, never labels.
- [Risk] `decode-or-error` raises where 1.0 returned fallbacks, surfacing as
  new `DocumentationInaccessibility` on previously tolerated inputs. →
  Mitigation: boundary tests for binary/non-textual inputs on both schemes;
  document behavior in the new spec.
- [Risk] Pyfakefs tests execute no detectors by construction, so a
  detextive-side detection regression would not fail them. → Mitigation:
  the real-filesystem smoke subset runs production-default Behaviors end
  to end over representative fixtures (utf-8, alternate charset, binary,
  empty).

## Migration Plan

Single change, behind no flag: dependency bump, call-site rewrite, helper
deletion, test reconfiguration. Validation is the existing suite
(`hatch --env develop run testers`) plus new boundary tests. Rollback is
`git revert` of the implementation commit; the 1.0 API remains installed
nowhere after the bump, so a revert must also restore the pin.

## Open Questions

- None blocking. Detextive Owner offered follow-ups during implementation;
  route behavioral surprises (e.g., unexpected `TextInvalidity` on real doc
  fixtures) back to them before encoding workarounds.
