# Robots.txt Compliance Design

## Overview

Implement robots.txt compliance in the cacheproxy module to ensure respectful web scraping when making multiple HTTP requests to external documentation sites.

## Core Components

### RobotsTxtCache
- Similar structure to existing ProbesCache and ContentsCache
- Cache parsed robots.txt per domain using `urllib.robotparser.RobotFileParser`
- TTL-based expiration (respect robots.txt Cache-Control when available)
- Graceful fallback if robots.txt fetch fails

### Integration Points
- Add robots.txt checking to `_probe_url` and `_retrieve_url` functions
- Fetch, parse, and cache robots.txt on first request to a domain
- Check crawl delay timestamps before making requests
- Skip URLs that are disallowed by robots.txt

### Crawl Delay Logic
1. Check if we have cached robots.txt for the domain
2. If not, fetch and parse robots.txt in parallel with first request
3. Check for active crawl delay timestamp for the site
4. If crawl delay active and not expired, async sleep until expiration
5. Perform the actual request
6. Set new crawl delay timestamp if robots.txt specifies Crawl-delay

### User-Agent Compliance
- Use consistent User-Agent string (e.g., "sphinxmcps/1.0 (+https://github.com/...)")
- Allow configuration of User-Agent for different contexts
- Pass User-Agent to RobotFileParser.can_fetch()

## Edge Cases

- Local file URLs (skip robots.txt checks)
- Sites without robots.txt (allow by default)
- Malformed robots.txt (log warning, allow by default)
- robots.txt fetch timeout (~5s, don't block main requests)
- Rate limiting hints in robots.txt (implement Crawl-delay)

## Performance Considerations

- Domain-level caching to avoid repeated robots.txt requests
- Parallel fetch of robots.txt with first URL request per domain
- Don't block on robots.txt if it takes too long
- Log compliance decisions for debugging

## Future Enhancements

- Respect Cache-Control headers from robots.txt responses
- Support for Sitemap directives
- More sophisticated rate limiting based on robots.txt hints

## Implementation Notes

- Use stdlib `urllib.robotparser.RobotFileParser`
- Follow existing cacheproxy patterns for cache structure
- Maintain backward compatibility with existing cache behavior
- Add appropriate logging for compliance decisions and edge cases