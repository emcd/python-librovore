# Detection Module Testing Plan

## Overview

The detection module handles processor selection, caching, and confidence-based decision making. **Current coverage: 28%** (27/96 lines) with significant gaps in core functionality.

## Architecture Summary

The detection system consists of:
- `interfaces.Detection` - Protocol for processor-specific detection results  
- `detection.DetectionsCacheEntry` - Cache storage with TTL and best detection logic
- `detection.DetectionsCache` - Main cache with dependency injection support
- `detection.determine_processor_optimal()` - Public API for processor selection

## Actual Coverage Gaps (from latest coverage report)

**NOTE: This analysis is based on actual missing lines from coverage report, not speculation.**

### 1. **DetectionsCacheEntry** ❌ *Lines 51-56, 60*
- `best_detection()` property - completely untested
- `is_expired()` method - completely untested
- These are core cache functionality

### 2. **DetectionsCache Public Interface** ❌ *Lines 74-80, 86-92, 98-103, 107-108, 114-116*
- `access_entry()` - cache miss, expiration cleanup
- `access_best_detection()` - delegation to cache entry
- `add_entry()` - timestamp generation and storage
- `clear()` - full cache reset
- `remove_entry()` - removal with return values

### 3. **Main Public API** ❌ *Lines 128-132*
- `determine_processor_optimal()` - **completely untested**
- Cache hit scenarios
- Cache miss → processor execution → selection flow

### 4. **Internal Functions** ❌ *Lines 139-158, 165-177*
- `_execute_processors()` - **completely untested** 
- `_select_processor_optimal()` - **completely untested**
- These represent the core selection algorithm

## Revised Testing Strategy

**Following project guidelines: test lower-level components first, avoid testing internal functions, use local documentation.**

### **Test Function Organization** (`test_200_detection.py`)

#### Series 100: DetectionsCacheEntry Tests 
```python
# Target Lines: 51-56, 60 (currently missing)
def test_100_cache_entry_best_detection_empty_returns_absent():
def test_110_cache_entry_best_detection_zero_confidence_returns_absent():
def test_120_cache_entry_best_detection_highest_confidence_wins():
def test_130_cache_entry_best_detection_tied_confidence_deterministic():
def test_140_cache_entry_is_expired_fresh_entry_returns_false():
def test_150_cache_entry_is_expired_expired_entry_returns_true():
def test_160_cache_entry_is_expired_boundary_condition():
```

#### Series 200: DetectionsCache Tests
```python
# Target Lines: 74-80, 86-92, 98-103, 107-108, 114-116 (currently missing)
def test_200_cache_access_entry_missing_returns_absent():
def test_210_cache_access_entry_fresh_returns_detections():
def test_220_cache_access_entry_expired_cleans_and_returns_absent():
def test_230_cache_access_best_detection_delegates_to_entry():
def test_240_cache_add_entry_stores_with_timestamp():
def test_250_cache_add_entry_overwrites_existing():
def test_260_cache_remove_entry_missing_returns_absent():
def test_270_cache_remove_entry_existing_returns_detections():
def test_280_cache_clear_empties_all_entries():
def test_290_cache_integration_add_access_expire_cycle():
```

#### Series 300: determine_processor_optimal Tests
```python
# Target Lines: 128-132 (currently missing - HIGHEST IMPACT)
def test_300_determine_processor_cache_hit_returns_cached():
def test_310_determine_processor_cache_miss_executes_processors():
def test_320_determine_processor_empty_registry_returns_absent():
def test_330_determine_processor_zero_confidence_returns_absent():
def test_340_determine_processor_highest_confidence_wins():
def test_350_determine_processor_confidence_tie_registration_order():
def test_360_determine_processor_stores_results_in_cache():
def test_370_determine_processor_dependency_injection():
```

#### Series 700: Sphinx Integration Tests (Future - Deferred)
```python
# Use .auxiliary/artifacts/sphinx-html for reliable testing
def test_710_sphinx_processor_detect_local_objects_inv():
def test_720_sphinx_processor_confidence_scoring():
def test_730_sphinx_processor_metadata_extraction():
def test_740_sphinx_integration_with_determine_processor():
```

## Mock Strategy (Simplified)

### **Core Mocks Needed:**
1. **MockDetection** - Simple dataclass implementing interfaces.Detection
2. **MockProcessor** - Returns configurable Detection objects from detect()
3. **Time Mocking** - For TTL expiration testing via unittest.mock.patch

### **Test Fixtures:**
1. **detection_samples** - Various confidence/metadata combinations
2. **processor_registry** - Small registry with 2-3 mock processors
3. **cache_fixture** - Fresh DetectionsCache instances

## Final Test File Structure

```
tests/test_000_sphinxmcps/
├── test_200_detection.py                 # All detection module functionality
│   ├── test_100_<name> series            # DetectionsCacheEntry tests
│   ├── test_200_<name> series            # DetectionsCache tests  
│   ├── test_300_<name> series            # determine_processor_optimal tests
│   └── (future: test_700_<name> series)  # Sphinx integration (deferred)
```

## Success Criteria

### **Minimum Acceptable Coverage:**
- [ ] Target **95%+ coverage on detection.py** (from current 28%)
- [ ] **All missing lines covered**: 51-56, 60, 74-80, 86-92, 98-103, 107-108, 114-116, 128-132
- [ ] **determine_processor_optimal() completely tested** (highest impact)
- [ ] Cache TTL and expiration logic verified
- [ ] Integration with real SphinxProcessor using local artifacts

### **Quality Gates:**
- [ ] All edge cases identified and tested (empty inputs, zero confidence, etc.)
- [ ] Proper error handling (absent returns, graceful failures)
- [ ] No reliance on internal function testing
- [ ] Integration with existing test patterns

### **AVOID (per project guidelines):**
- ❌ Testing internal functions `_execute_processors()` and `_select_processor_optimal()`
- ❌ Integration tests against live external sites
- ❌ Complex concurrency testing (not needed for coverage goals)
- ❌ Over-engineering mock systems

## Implementation Notes

### **Testing Framework:**
- Use existing pytest + Mock patterns from xtnsmgr tests
- Follow function-based test style (not classes)
- Use descriptive test names: `test_cache_entry_expired_returns_absent`

### **Test Data:**
- Use `.auxiliary/artifacts/sphinx-html/objects.inv` for real integration
- Create realistic source URLs: `"file:///path/to/docs"`, `"https://docs.python.org"`
- Use varied confidence values (0.0, 0.3, 0.7, 0.95, 1.0)

### **Key Insights from Coverage Analysis:**
1. **Most missing coverage (49/76 lines) is in public methods** - perfect for testing
2. **Main API completely untested** - huge impact opportunity  
3. **Current architecture already supports dependency injection** - testing should be straightforward
4. **Local Sphinx artifacts available** - reliable integration testing possible

This focused plan targets actual coverage gaps while following project guidelines and avoiding over-engineering.