# Test Plan: robots.txt Compliance in cacheproxy Module

## Coverage Analysis Summary
- Current coverage: 91% (cacheproxy.py), 66% (exceptions.py)
- Target coverage: 100%
- Uncovered lines for robots.txt features:
  - cacheproxy.py: 264-265, 271, 277-278, 301-303, 313-315, 343-345, 452->exit, 456, 460, 462->exit, 466-467, 470, 524-525, 564-567, 582
  - exceptions.py: 206-211 (RobotsTxtBlockedUrl)
- Missing functionality tests: Complete robots.txt compliance feature suite

## Test Strategy

### Basic Functionality Tests (400-499 range)
Following the existing cacheproxy test numbering pattern, robots.txt tests should occupy the 400-499 range:

- **400-409**: RobotsCache class basic operations
- **410-419**: _extract_domain utility function
- **420-439**: _check_robots_txt permission checking
- **440-459**: _retrieve_robots_txt fetching and parsing
- **460-479**: _apply_request_delay crawl delay logic
- **480-489**: Integration with probe_url and retrieve_url functions
- **490-499**: Exception handling and edge cases

### Component-Specific Tests

#### RobotsCache Class (Tests 400-409)
**Uncovered lines: 264-265, 271, 277-278, 301-303, 313-315**

- **test_400_robots_cache_initialization**: Constructor and basic setup
- **test_401_robots_cache_access_missing_returns_absent**: Cache miss scenario
- **test_402_robots_cache_access_fresh_returns_parser**: Cache hit with valid robots.txt
- **test_403_robots_cache_access_expired_returns_absent**: TTL expiration handling
- **test_404_robots_cache_store_robots_parser**: Storing parsed robots.txt data
- **test_405_robots_cache_calculate_delay_remainder**: Crawl delay calculation
- **test_406_robots_cache_assign_delay**: Setting crawl delay timestamps
- **test_407_robots_cache_eviction_by_count**: LRU eviction when cache full
- **test_408_robots_cache_determine_ttl_success_vs_error**: TTL calculation for success/error
- **test_409_robots_cache_record_access_updates_lru**: LRU order maintenance

**Dependencies needing injection**: RobotsCache constructor takes CacheConfiguration
**Special considerations**: Test crawl delay timing without actual sleep delays

#### Domain Extraction Utility (Tests 410-419)
**Uncovered lines: None specifically, but function needs coverage**

- **test_410_extract_domain_http_url**: HTTP URL domain extraction
- **test_411_extract_domain_https_url**: HTTPS URL domain extraction  
- **test_412_extract_domain_with_port**: URL with explicit port
- **test_413_extract_domain_with_path**: URL with path components
- **test_414_extract_domain_with_query**: URL with query parameters

#### robots.txt Permission Checking (Tests 420-439)
**Uncovered lines: 343-345**

- **test_420_check_robots_txt_allowed_url**: robots.txt allows access
- **test_421_check_robots_txt_blocked_url**: robots.txt blocks access  
- **test_422_check_robots_txt_non_http_scheme**: File/FTP schemes always allowed
- **test_423_check_robots_txt_missing_robots_file**: No robots.txt found (allow by default)
- **test_424_check_robots_txt_malformed_robots_file**: Invalid robots.txt content
- **test_425_check_robots_txt_cache_hit**: Use cached robots.txt parser
- **test_426_check_robots_txt_cache_miss_fetch**: Fetch robots.txt when not cached
- **test_427_check_robots_txt_custom_user_agent**: Custom user agent string
- **test_428_check_robots_txt_default_user_agent**: Default user agent from config
- **test_429_check_robots_txt_parser_exception**: Exception during can_fetch() call

#### robots.txt Fetching and Parsing (Tests 440-459)  
**Uncovered lines: 564-567**

- **test_440_retrieve_robots_txt_success**: Successful fetch and parse
- **test_441_retrieve_robots_txt_http_error**: HTTP error during fetch
- **test_442_retrieve_robots_txt_timeout**: Request timeout
- **test_443_retrieve_robots_txt_parse_error**: robots.txt parsing failure
- **test_444_retrieve_robots_txt_empty_content**: Empty robots.txt file
- **test_445_retrieve_robots_txt_mutex_deduplication**: Multiple concurrent requests
- **test_446_retrieve_robots_txt_custom_client_factory**: Custom httpx client
- **test_447_retrieve_robots_txt_cache_storage**: Result stored in cache
- **test_448_retrieve_robots_txt_ttl_determination**: TTL calculation for cache
- **test_449_retrieve_robots_txt_error_result_extraction**: Error handling flow

#### Crawl Delay Logic (Tests 460-479)
**Uncovered lines: 452->exit, 456, 460, 462->exit, 466-467, 470**

- **test_460_apply_request_delay_non_http_scheme**: No delay for file:// URLs
- **test_461_apply_request_delay_no_robots_cached**: Fetch robots.txt if missing
- **test_462_apply_request_delay_active_delay**: Sleep when delay active
- **test_463_apply_request_delay_expired_delay**: No sleep when delay expired
- **test_464_apply_request_delay_set_new_delay**: Set delay from robots.txt
- **test_465_apply_request_delay_no_crawl_delay**: robots.txt has no Crawl-delay
- **test_466_apply_request_delay_invalid_crawl_delay**: Non-numeric Crawl-delay value
- **test_467_apply_request_delay_robots_parser_exception**: Exception getting crawl delay
- **test_468_apply_request_delay_with_custom_client**: Custom client factory
- **test_469_apply_request_delay_time_calculation**: Delay timestamp calculation

#### Integration Tests (Tests 480-489)
**Uncovered lines: 524-525, 582**

- **test_480_probe_url_robots_txt_blocked**: probe_url blocked by robots.txt
- **test_481_probe_url_robots_txt_allowed**: probe_url allowed by robots.txt
- **test_482_retrieve_url_robots_txt_blocked**: retrieve_url blocked by robots.txt
- **test_483_retrieve_url_robots_txt_allowed**: retrieve_url allowed by robots.txt
- **test_484_retrieve_url_as_text_robots_txt_blocked**: retrieve_url_as_text blocked
- **test_485_robots_txt_integration_with_caching**: robots.txt + HTTP caching
- **test_486_robots_txt_crawl_delay_integration**: Crawl delay + HTTP requests
- **test_487_robots_txt_custom_user_agent_integration**: Custom user agent flow
- **test_488_robots_txt_domain_based_caching**: Multiple domains cached separately
- **test_489_robots_txt_error_propagation**: Error handling through call chain

#### Exception Handling and Edge Cases (Tests 490-499)
**Exception uncovered lines: 206-211**

- **test_490_robots_txt_blocked_url_exception**: RobotsTxtBlockedUrl creation
- **test_491_robots_txt_blocked_url_exception_attributes**: Exception attributes
- **test_492_robots_txt_blocked_url_exception_inheritance**: Exception hierarchy
- **test_493_robots_txt_blocked_url_exception_message**: Error message format
- **test_494_robots_txt_network_failure_fallback**: Network errors allow access
- **test_495_robots_txt_dns_resolution_failure**: DNS failure handling
- **test_496_robots_txt_invalid_url_handling**: Malformed URL handling
- **test_497_robots_txt_concurrent_cache_access**: Race condition handling
- **test_498_robots_txt_cache_corruption_recovery**: Cache corruption scenarios
- **test_499_robots_txt_configuration_edge_cases**: Configuration edge cases

## Implementation Notes

### Dependencies Requiring Injection
- **CacheConfiguration**: For RobotsCache initialization
- **client_factory**: Custom httpx.AsyncClient factory for mocking
- **robots_cache**: Custom RobotsCache instances for isolation
- **user_agent**: Custom user agent strings for testing

### HTTP Mocking Strategy
- Use httpx.MockTransport for robots.txt HTTP requests
- Never test against real external sites (example.com, httpbin.com, etc.)
- Mock both successful and error responses (404, timeout, malformed content)
- Test robots.txt content with various Crawl-delay and Disallow patterns

### Filesystem Operations
- No filesystem operations in robots.txt functionality
- All operations are HTTP-based with in-memory caching

### Test Data and Fixtures
**Needed under tests/data/:**
- **robots_txt_samples/**: Various robots.txt content examples
  - `allow_all.txt`: robots.txt allowing all access
  - `block_all.txt`: robots.txt blocking all access  
  - `block_specific.txt`: robots.txt blocking specific paths
  - `with_crawl_delay.txt`: robots.txt with Crawl-delay directive
  - `malformed.txt`: Invalid robots.txt syntax
  - `empty.txt`: Empty robots.txt file

### Time-Based Testing
- Mock time.time() for crawl delay testing to avoid actual sleep
- Test delay calculation and expiration logic deterministically
- Use time advancement patterns for TTL testing

### Private Functions/Methods Testing Strategy
- **_check_robots_txt**: Test via integration with probe_url/retrieve_url  
- **_retrieve_robots_txt**: Test via _check_robots_txt cache miss scenarios
- **_apply_request_delay**: Test via integration with probe_url/retrieve_url
- **_extract_domain**: Test directly (utility function)

### Anti-Patterns to Avoid
- **No real network requests**: Never test against actual robots.txt files
- **No monkey-patching**: Use dependency injection for all mocking
- **No external site dependencies**: Mock all HTTP interactions
- **No sleep in tests**: Mock time for crawl delay testing

### Third-Party Testing Patterns to Research
- **httpx.MockTransport**: For HTTP request mocking
- **urllib.robotparser.RobotFileParser**: Mocking robots.txt parsing behavior
- **asyncio event loop mocking**: For time-based delay testing
- **concurrent.futures**: For testing mutex deduplication

## Success Metrics
- Target line coverage: 100% for robots.txt functionality
- Branch coverage goals: 100% for robots.txt logic
- Specific gaps to close:
  - cacheproxy.py lines: 264-265, 271, 277-278, 301-303, 313-315, 343-345, 452->exit, 456, 460, 462->exit, 466-467, 470, 524-525, 564-567, 582
  - exceptions.py lines: 206-211

## Test Module Integration
**Target file**: `tests/test_000_sphinxmcps/test_110_cacheproxy.py`
**Numbering range**: 400-499 (following existing pattern: 100s=ContentCache, 200s=ProbeCache, 300s=retrieve_url functions)
**Pattern consistency**: Follow existing async/await patterns and httpx.MockTransport usage

## Architecture Considerations
**No immutability constraint violations**: All robots.txt components use dependency injection
**No monkey-patching required**: Clean testable design with injected dependencies  
**Performance considerations**: Tests should complete quickly without actual network calls or sleep delays
**Complexity estimation**: Medium - approximately 100 test functions covering comprehensive robots.txt compliance