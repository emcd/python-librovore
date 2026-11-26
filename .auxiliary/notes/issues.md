# Librovore Issues and Enhancement Opportunities

## SSL/TLS Certificate Verification Failure

**Date Reported**: 2025-11-19
**Component**: Sphinx inventory processor (urllib-based inventory download)
**Severity**: Medium (blocks testing with some sites)

### Issue Description

When attempting to fetch Sphinx object inventories from certain sites (e.g., `docs.twistedmatrix.com`, `www.dulwich.io`), the inventory processor fails with:

```
<urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
self-signed certificate in certificate chain (_ssl.c:1017)>
```

### Observed Behavior

- ✅ **Detection/probing via httpx**: Successfully connects to sites (HEAD/GET for HTML)
- ❌ **Inventory download via urllib**: Fails SSL verification

### Root Cause

The certificate chains for these documentation sites include self-signed certificates. Different SSL handling between:
- **httpx** (used for detection): More lenient or different SSL context
- **urllib** (used in Sphinx inventory processor): Strict SSL verification against system CA bundle

### Impact

- **Structure processors** (including new Pydoctor processor) cannot be fully tested end-to-end with these sites
- **Inventory processor** cannot fetch inventory files from affected sites
- Does not affect sites with properly signed certificates

### Affected Sites

- https://docs.twistedmatrix.com/en/stable/api/
- https://www.dulwich.io/api/

### Potential Solutions

1. **Configure httpx-based inventory fetching** to use same client as detection
2. **Add SSL verification configuration** to allow disabling verification for specific domains (testing only)
3. **Report to site maintainers** about certificate chain issues
4. **Use different inventory sources** (manual creation, alternative processors)

### Notes

This issue was discovered during Pydoctor structure processor testing. The structure processor implementation is correct and works properly when inventory objects are available from other sources.

---

## Code Duplication: normalize_base_url

**Date Reported**: 2025-11-19
**Component**: Structure processors (Sphinx, Pydoctor)
**Severity**: Low (technical debt)

### Issue Description

The `normalize_base_url` function is duplicated across structure processor packages:
- `sources/librovore/structures/sphinx/urls.py`
- `sources/librovore/structures/pydoctor/urls.py`

### Current State

Both implementations are identical and handle:
- URL parsing and normalization
- File path to URL conversion
- Scheme validation (http, https, file)
- Path cleanup (trailing slash removal)

### Recommendation

Extract `normalize_base_url` and related URL utilities to a shared location:
- Option 1: `sources/librovore/structures/urls.py` (common module)
- Option 2: `sources/librovore/urls.py` (top-level utility)
- Option 3: Include in base structure processor class

### Benefits

- Reduces code duplication
- Ensures consistent URL handling across all structure processors
- Simplifies maintenance and testing
- Reduces risk of divergence between implementations

### Impact

Low priority - current duplication is manageable with only two instances. Should be addressed before adding more structure processors to prevent further duplication.
