Below is a concise **design extraction** from the provided source, followed by a **design review** with strengths, risks, and concrete improvements.

---

## 1) Design extraction

### Purpose

A **Model Context Protocol (MCP) server** that lets clients (LLMs, tools, humans via CLI) **inspect and query Sphinx‑generated documentation**—either locally (file://) or over HTTP(S). It exposes:

* A **CLI** for ad‑hoc use, and
* An **MCP server** (FastMCP) with tools to explore/query docs.

### High‑level architecture

```
librovore/
├─ __/                         # Common imports, logging, CLI display, doctext
├─ exceptions.py               # Domain exception types
├─ interfaces.py               # Public Processor / Detection interfaces + Filters
├─ xtnsapi.py                  # Processor registry & public re-exports
├─ cacheproxy.py               # HTTP/file retrieval + caching (GET/HEAD)
├─ functions.py                # Core business logic used by CLI and server
├─ detection.py                # (Alt) detection cache & selection policy (unused)
├─ server.py                   # FastMCP server surface (tools)
├─ cli.py                      # Tyro-based CLI (use/explore/query/serve)
└─ xtnsmgr/                    # Extension manager (load/register processors)
   ├─ configuration.py         # Read/validate config; split intrinsic/external
   ├─ installation.py          # Async install external ext. with `uv`
   ├─ cachemgr.py              # On-disk cache of installed packages
   ├─ importation.py           # sys.path & .pth handling for ext.
   └─ processors/              # Built-in processors
      └─ sphinx/               # SphinxProcessor implementation
         ├─ main.py            # Detect/extract inventory/docs/query
         ├─ inventory.py       # objects.inv filtering (exact/regex/fuzzy)
         ├─ extraction.py      # HTML parsing (signature/description)
         ├─ conversion.py      # HTML→Markdown cleanup
         └─ urls.py            # URL normalization & derivations
```

### Core concepts & data model

* **Filters** (`interfaces.Filters`): `domain`, `role`, `priority`, `match_mode` (`Exact|Regex|Fuzzy`), `fuzzy_threshold`.
* **Processor** interface: `detect`, `extract_inventory`, `extract_documentation`, `query_documentation`.
* **SphinxProcessor**: built‑in processor that:

  * *Detects* Sphinx via presence of `objects.inv` (and boosts confidence if `searchindex.js` is present). Optional, coarse **theme detection** (furo, alabaster, rtd).
  * *Inventory*: loads `objects.inv` (via `sphobjinv`) and filters by `Filters` (exact/regex/fuzzy using `sphobjinv.suggest()`).
  * *Documentation*: derives object page URL/fragment, downloads HTML, parses to `(signature, description)`, and converts description to lightweight Markdown.
  * *Query*: pre‑scores candidates by name/priority, retrieves top pages concurrently, computes relevance (name/signature/description hits) and optional snippets, then ranks and returns.

### Retrieval and caching

* **cacheproxy** provides:

  * `probe_url(ParseResult)->bool`: cached `HEAD`/existence check (HTTP) or filesystem existence for `file://` and paths.
  * `retrieve_url(ParseResult)->bytes` and `retrieve_url_as_text(...)->str`: cached `GET` with per‑URL request **deduplication** using `asyncio.Lock`.
* **ContentCache** (GET):

  * Size‑bounded (default 32 MiB), **LRU** eviction (deque).
  * TTL based on success vs error.
* **ProbeCache** (HEAD):

  * Entry‑count‑bounded (default 1000), **LRU** eviction by count.
  * TTL based on success vs error.

### Business logic façade (used by CLI & MCP tools)

* `explore(source, query, filters, max_objects, include_documentation)`:

  * Extract inventory → pick top objects (by fuzzy score) → optionally fetch docs → return unified structure with metadata.
* `query_documentation(source, query, filters, max_results, include_snippets)`:

  * Uses processor’s `query_documentation`, then shapes into a uniform “explore-style” result payload.
* `summarize_inventory(source, term, filters)`:

  * High‑level summary (project, version, counts, per‑domain).

### Extensibility

* **Processor registry** (`xtnsapi.processors`): `ValidatorDictionary[str, Processor]`.
* **Extension manager** (`xtnsmgr`):

  * Reads config (`extensions` list with `name`, optional `package`, `enabled`, `arguments`).
  * **Intrinsic** (built‑in) vs **external** (pip/uv‑installed) extensions.
  * Installs external packages under `.auxiliary/caches/extensions/<hash>/<platform>`, adds to `sys.path`, processes `.pth`.
  * Imports module and calls its `register(arguments)` to add to the registry.

### Surfaces

* **CLI** (`tyro`):

  * `use summarize-inventory`, `use query-documentation`, `use explore`
  * `serve` (starts MCP server; CLI boot path also registers processors)
* **MCP server**:

  * Registers tools: `summarize_inventory`, `query_documentation`, `explore`.
  * Transport: `stdio` (default) or `sse`.

---

## 2) Design review

### What’s strong

1. **Clean separation of concerns**

   * Retrieval/caching (cacheproxy) is isolated from domain logic (SphinxProcessor) and from orchestration (functions, server, CLI).
   * Domain‑specific errors make failures explicit and debuggable.

2. **Extensibility**

   * Processor interface and a registry allow drop‑in support for other doc systems.
   * External processors can be installed on‑demand with isolation to a cache directory.

3. **Performance‑aware**

   * Per‑URL request **deduplication**; LRU caches with TTLs; **pre‑scoring** candidates to limit HTTP fan‑out; **parallel** fetch of candidate docs.

4. **Useful surfaces**

   * Consistent structures returned by `explore` and `query_documentation`.
   * CLI mirrors MCP tools for local workflows.

### Risks / weaknesses & why they matter

1. ✅ ~~**Two detection paths; only one is used**~~ **RESOLVED**

   * ~~`functions._select_processor_for_source` does ad‑hoc per‑call iteration over all processors and calls `detect()` each time.~~
   * ~~There is a richer `detection.py` with a **DetectionsCache** and ordering policy, but it is **not used**.~~
   * ~~*Impact*: duplicate logic, extra HEAD/GET traffic, missed cache benefits.~~
   * **Status**: Detection is now unified and working correctly with proper caching.

2. ✅ ~~**Ambiguous naming in caching**~~ **RESOLVED**

   * ~~`CacheEntry.extant` returns `True` when the entry is **expired** (per docstring), and code treats it as such. The name "extant" reads as "still valid".~~
   * ~~*Impact*: maintainability trap; future changes may invert logic accidentally.~~
   * **Status**: Fixed with clear `CacheEntry.invalid` property using `time() - timestamp > ttl`.

3. **TTL policy is under‑specified**

   * `CacheConfiguration.network_error_ttl` exists but is **unused**; all errors get `error_ttl`.
   * *Impact*: repeated rapid retries for transient network errors or, conversely, overly long back‑offs for HTTP 4xx vs timeouts.

4. **HTTP client reuse**

   * A new `httpx.AsyncClient()` is created per request; keep‑alive pooling is not reused across calls.
   * *Impact*: unnecessary connection setup & TLS handshakes under load.

5. ✅ ~~**HTML parsing assumptions**~~ **FULLY RESOLVED**

   * ~~`extraction.parse_documentation_html` assumes `article[role="main"]` and specific Sphinx markup (`dt/dd`, `section`), and `conversion` does coarse HTML→MD.~~
   * ~~*Impact*: Theme variations or non‑standard Sphinx pages can fail parsing or degrade quality. Limited theme detection (string contains furo/alabaster/rtd) is brittle.~~
   * **Status**: **COMPLETELY RESOLVED** with DSL-driven content extraction:
     - Theme-specific extraction patterns (Furo, pydoctheme, ReadTheDocs, custom themes)
     - Configurable content strategies per theme and element type
     * Generic fallback patterns for unknown themes
     * Single-pass HTML-to-Markdown conversion with proper spacing preservation
     * Tested successfully across all major Sphinx themes

6. **Security posture of `.pth` processing** *(DEFERRED)*

   * `.pth` lines beginning with `import` are executed.
   * *Impact*: This mirrors Python's own `.pth` behavior, but increases **supply‑chain risk** for untrusted extension packages.

7. ✅ ~~**Result typing ergonomics**~~ **RESOLVED**

   * ~~Some functions return dicts that may contain an `'error'` string; others raise typed exceptions.~~
   * ~~*Impact*: Mixed error patterns complicate downstream handling.~~
   * ~~**Note**: This is the primary remaining issue from testing - users get generic "Error executing tool explore" messages instead of meaningful, actionable error descriptions.~~
   * **Status**: **FULLY IMPLEMENTED** structured error handling system:
     - Fixed inconsistent error patterns (no more `{'error': '...'}` returns)
     - All exceptions now follow consistent exception-based model
     - MCP server tools return structured error responses with error_type, message, details, and actionable suggestions
     - CLI shows user-friendly error messages with emojis and suggestions
     - Comprehensive error coverage for all major exception types
     - Both LLMs and CLI users get meaningful, actionable error information

8. **Relevance and snippet scoring**

   * Heuristics are simple (contains query in name/signature/description with fixed weights).
   * *Impact*: Good baseline, but may need normalization or BM25‑like scoring for larger corpora.

9. **Charset & content-type handling**

   * `retrieve_url_as_text` relies on `Content-Type` charset; no HTML meta fallback.
   * `HttpContentTypeInvalidity` is raised when mimetype isn't in a fixed allowlist.
   * *Impact*: Some servers omit charset or return generic types; strictness may cause avoidable failures.

10. ✅ ~~**Inventory fuzzy matching**~~ **RESOLVED**

    * ~~Uses `sphobjinv.suggest()`; when `with_score=False` the code sets all matches to `fuzzy_threshold` as score.~~
    * ~~*Impact*: Score ordering may be coarse; combination with query ranking could be improved.~~
    * **Status**: Fuzzy matching is working well with proper scoring and ranking.

### Concrete recommendations (prioritized)

1. ✅ ~~**Unify detection & cache results**~~ **RESOLVED**

   * ~~Replace `functions._select_processor_for_source` with `detection.determine_processor_optimal(...)`.~~
   * ~~Keep a module‑level `DetectionsCache` and **reuse** detections across requests.~~
   * ~~Consider initializing detections during CLI/MCP startup for configured sources.~~

2. ✅ ~~**Fix naming & TTL policy in caches**~~ **PARTIALLY RESOLVED**

   * ✅ ~~Rename `CacheEntry.extant` → `expired` (and invert use) or update property to `not expired`.~~
   * ⏳ Use **distinct TTLs**: *(still to be implemented)*
     * success (2–10 min),
     * HTTP 4xx/5xx (e.g., 60–120 s),
     * network/timeouts/DNS (short, e.g., 10–30 s using `network_error_ttl`).
   * ⏳ Optionally store a lightweight **status enum** in entries to set TTL precisely.

3. **Reuse HTTP clients**

   * Provide an `AsyncClient` pool or a single shared `httpx.AsyncClient` per process with proper lifetime management (context at server startup).
   * Keep request‑level timeouts; still deduplicate with per‑URL locks.

4. ✅ ~~**Parsing robustness**~~ **LARGELY RESOLVED**

   * ⏳ Fallback parser: if `lxml` unavailable or parse fails, retry with `html.parser`. *(minor enhancement)*
   * ✅ ~~Make the main content selector **configurable** by theme (e.g., lookup table for common themes).~~
   * ✅ ~~When deriving the element to extract, if the `id` anchor is missing, search by nearest header anchors or by linkbacks.~~
   * **Status**: DSL implementation handles theme variations and content extraction robustly.

5. **Safer `.pth` handling** *(DEFERRED)*

   * Allow `.pth` processing only for **trusted origins** (e.g., allow‑list packages or a configuration flag).
   * Alternatively, **ignore import lines** in `.pth` and only add paths (common enough for wheels).

6. **MIME/charset resilience**

   * If `Content-Type` is missing/unknown and the resource looks like text (`<html` prefix), proceed with a heuristic decode (`utf‑8`, backoff to `latin‑1`) and **warn** rather than hard‑fail.
   * Parse `<meta charset>` or `<meta http-equiv="content-type">` as a fallback.

7. ✅ ~~**Ranking improvements**~~ **MOSTLY RESOLVED**

   * ✅ ~~Normalize scores (min‑max) and combine inventory fuzzy score with content relevance.~~
   * ⏳ Add simple proximity boosts (query near start of signature/title). *(enhancement)*
   * ⏳ Add a light **BM25** or TF‑IDF on paragraph chunks (kept in memory per page) if performance allows. *(enhancement)*
   * **Status**: Current ranking system works well for tested use cases.

8. ✅ ~~**Consistent error model**~~ **RESOLVED**

   * ✅ ~~Prefer **exceptions** for exceptional flows; keep result payloads free of `'error'` fields.~~
   * ✅ ~~Map exceptions at the server boundary to structured MCP error responses.~~
   * **Status**: **FULLY IMPLEMENTED** - complete structured error handling system with meaningful, actionable error messages for both MCP server and CLI interfaces.

9. **Configuration clarity**

   * For external processors, config uses `name` as module path and `package` as pip spec; document this explicitly.
   * Validate that a module's `register(arguments)` actually registers **exactly one** processor (helpful diagnostics).

10. **Observability**

* Emit metrics: cache hit/miss, eviction counts, network errors by type, average fetch ms.
* Add DEBUG logs for detection decisions (which processor, confidence, cache status).

11. **Tests to add**

* Unit tests for `urls.normalize_base_url` (file/HTTP edge cases).
* Cache eviction behavior (size & TTL).
* Parsing across a matrix of Sphinx themes (golden samples).
* Fuzzy vs regex filtering correctness with `sphobjinv`.
* End‑to‑end MCP tool calls against a small fixture site.

---

## 3) Quick “how it works” flows (for reference)

* **Server startup (CLI `serve`)**

  1. Prepare app env → load `extensions` → (optionally) install via `uv` → import & `register()` processors → start FastMCP with tools.

* **`explore` flow**

  1. Select best processor → load & filter `objects.inv` → pick top N by fuzzy score → (optional) fetch each doc, extract signature/description → return documents + search metadata.

* **`query_documentation` flow**

  1. Filter inventory → pre‑score candidates by name/priority → fetch top K pages concurrently → parse, compute relevance and snippet → sort & return.

* **Retrieval**

  * `probe_url` HEAD (or filesystem) through `ProbeCache`.
  * `retrieve_url(_as_text)` GET through `ContentCache`, per‑URL mutex, MIME/charset checks.

---

If you’d like, I can:

* Draft a small **diagram** (module + data flow).
* Provide a **patch** for the detection unification + cache naming/TTL changes.
* Add a **feature flag** for safer `.pth` handling.
