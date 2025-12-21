# Feature Plan: Robots.txt Compliance

> **Status**: 📋 Planning  
> **Priority**: High  
> **Estimated Effort**: Medium  
> **Target Version**: 2.2.0

## 📋 Overview

Implement robots.txt parsing and compliance checking to ensure Pricewatch respects website crawling policies. This feature will check robots.txt files before making scraping requests and prevent scraping when disallowed.

### Goals

- ✅ Respect robots.txt rules for all target websites
- ✅ Cache robots.txt files to minimize redundant requests
- ✅ Handle edge cases (missing robots.txt, malformed files, etc.)
- ✅ Provide clear error messages when scraping is disallowed
- ✅ Configurable compliance mode (strict vs. permissive)
- ✅ Logging and monitoring for compliance violations

### Non-Goals (Out of Scope)

- ❌ Sitemap.xml parsing (future enhancement)
- ❌ Crawl-delay enforcement (future enhancement)
- ❌ User-agent rotation (future enhancement)
- ❌ Robots.txt for non-HTTP protocols

---

## 🎯 Requirements

### Functional Requirements

1. **Robots.txt Fetching**
   - Fetch robots.txt from target website root
   - Handle HTTP errors gracefully (404, 500, etc.)
   - Support both HTTP and HTTPS
   - Follow redirects (max 3 redirects)

2. **Robots.txt Parsing**
   - Parse standard robots.txt format (RFC 9309)
   - Support multiple User-Agent groups
   - Handle wildcards in paths (`*`)
   - Support `Allow` and `Disallow` directives
   - Handle comments and empty lines
   - Support `Crawl-delay` directive (parse, log, but don't enforce initially)

3. **Rule Checking**
   - Check if specific URL path is allowed/disallowed
   - Match against longest matching rule
   - Default to allowed if no matching rule found
   - Support wildcard matching in paths

4. **Caching**
   - Cache parsed robots.txt files in memory
   - Cache TTL: 24 hours (configurable)
   - Invalidate cache on errors (optional)
   - Support cache warming for known domains

5. **Integration**
   - Check robots.txt before scraping in `get_price()`
   - Raise appropriate exception when disallowed
   - Provide user-friendly error messages
   - Log compliance checks for monitoring

### Non-Functional Requirements

1. **Performance**
   - Cache hit should be < 1ms
   - Cache miss (fetch + parse) should be < 2 seconds
   - Minimal impact on existing scraping performance

2. **Reliability**
   - Handle network timeouts gracefully
   - Handle malformed robots.txt files
   - Fallback behavior when robots.txt unavailable

3. **Configurability**
   - Enable/disable robots.txt checking
   - Strict vs. permissive mode
   - Custom User-Agent string
   - Cache TTL configuration

4. **Observability**
   - Log robots.txt fetch attempts
   - Log compliance violations
   - Metrics for cache hits/misses
   - Metrics for disallowed requests

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                  Scraper Module                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         RobotsTxtChecker (New)                   │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  RobotsTxtParser                           │  │  │
│  │  │  - Parse robots.txt format                 │  │  │
│  │  │  - Extract rules by User-Agent             │  │  │
│  │  │  - Match paths against rules               │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  RobotsTxtCache                            │  │  │
│  │  │  - In-memory cache (TTL-based)             │  │  │
│  │  │  - Cache invalidation                      │  │  │
│  │  │  - Thread-safe operations                  │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  RobotsTxtFetcher                          │  │  │
│  │  │  - HTTP/HTTPS fetching                     │  │  │
│  │  │  - Redirect handling                       │  │  │
│  │  │  - Error handling                          │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│                         ▼                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │         get_price() (Modified)                   │  │
│  │  - Check robots.txt before scraping             │  │
│  │  - Raise RobotsTxtDisallowedError if blocked    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### File Structure

```
app/
├── scraper.py              # Modified: Add robots.txt check
├── robots.py               # New: Robots.txt handling module
│   ├── RobotsTxtChecker    # Main interface
│   ├── RobotsTxtParser     # Parsing logic
│   ├── RobotsTxtCache      # Caching layer
│   └── RobotsTxtFetcher    # HTTP fetching
└── exceptions.py           # Modified: Add RobotsTxtDisallowedError
```

---

## 📝 Implementation Plan

### Phase 1: Core Infrastructure (Foundation)

#### 1.1 Create Robots.txt Module Structure
**Files**: `app/robots.py`

- [ ] Create `RobotsTxtFetcher` class
  - Method: `fetch_robots_txt(base_url: str) -> str`
  - Handle HTTP/HTTPS
  - Handle redirects (max 3)
  - Handle timeouts (use config timeout)
  - Return empty string on 404 (robots.txt not found = allowed)
  - Raise exception on other errors

- [ ] Create `RobotsTxtParser` class
  - Method: `parse(content: str) -> Dict[str, List[Rule]]`
  - Parse User-Agent groups
  - Parse Allow/Disallow rules
  - Parse Crawl-delay (store but don't enforce)
  - Handle comments (lines starting with `#`)
  - Handle empty lines
  - Handle wildcards in paths
  - Return structured rule data

- [ ] Create `Rule` dataclass
  - Fields: `path: str`, `allowed: bool`, `user_agent: str`
  - Methods: `matches(url_path: str) -> bool`

#### 1.2 Create Exception Class
**Files**: `app/exceptions.py`

- [ ] Add `RobotsTxtDisallowedError` exception
  - Inherit from `ScrapingError`
  - Include URL and reason in message
  - User-friendly error message

#### 1.3 Configuration
**Files**: `app/config.py`

- [ ] Add robots.txt settings:
  ```python
  # Robots.txt compliance
  robots_txt_enabled: bool = True
  robots_txt_strict_mode: bool = True  # True = block, False = warn only
  robots_txt_cache_ttl: int = 86400  # 24 hours in seconds
  robots_txt_user_agent: str = "Pricewatch/2.1.0"
  robots_txt_timeout: int = 5  # seconds
  ```

### Phase 2: Caching Layer

#### 2.1 Implement Cache
**Files**: `app/robots.py`

- [ ] Create `RobotsTxtCache` class
  - Thread-safe cache (use `threading.Lock`)
  - TTL-based expiration
  - Methods:
    - `get(domain: str) -> Optional[Dict]`
    - `set(domain: str, rules: Dict, ttl: int)`
    - `invalidate(domain: str)`
    - `clear()`
  - Store: `{domain: {rules: Dict, expires_at: float}}`

#### 2.2 Cache Integration
- [ ] Integrate cache with fetcher
  - Check cache before fetching
  - Store parsed results in cache
  - Handle cache expiration

### Phase 3: Rule Matching Logic

#### 3.1 Path Matching
**Files**: `app/robots.py`

- [ ] Implement path matching algorithm
  - Longest matching rule wins
  - Support wildcards (`*`)
  - Handle trailing slashes
  - Handle query strings (ignore for matching)
  - Handle URL encoding

- [ ] Implement User-Agent matching
  - Match specific User-Agent first
  - Fall back to `*` (all agents)
  - Case-insensitive matching

#### 3.2 Rule Evaluation
- [ ] Implement `is_allowed(url: str, user_agent: str) -> bool`
  - Extract domain and path from URL
  - Get rules for domain (from cache or fetch)
  - Match path against rules
  - Return True if allowed, False if disallowed
  - Default to True if no rules found

### Phase 4: Integration with Scraper

#### 4.1 Modify Scraper
**Files**: `app/scraper.py`

- [ ] Create `RobotsTxtChecker` class
  - Initialize with config
  - Method: `check_url(url: str) -> None`
  - Raise `RobotsTxtDisallowedError` if disallowed
  - Log compliance checks

- [ ] Integrate into `get_price()`
  - Check robots.txt at start of function
  - Only proceed if allowed
  - Handle exceptions appropriately

#### 4.2 Error Handling
- [ ] Update error handling in `get_price()`
  - Catch `RobotsTxtDisallowedError`
  - Return appropriate error message
  - Log violation for monitoring

### Phase 5: Logging & Monitoring

#### 5.1 Logging
**Files**: `app/robots.py`, `app/scraper.py`

- [ ] Add logging for:
  - Robots.txt fetch attempts
  - Cache hits/misses
  - Compliance violations
  - Parsing errors
  - Network errors

#### 5.2 Metrics (Optional - Future)
**Files**: `app/monitoring.py`

- [ ] Add Prometheus metrics:
  - `pricewatch_robots_txt_fetches_total`
  - `pricewatch_robots_txt_cache_hits_total`
  - `pricewatch_robots_txt_disallowed_total`
  - `pricewatch_robots_txt_fetch_duration_seconds`

### Phase 6: Testing

#### 6.1 Unit Tests
**Files**: `tests/test_robots.py`

- [ ] Test `RobotsTxtParser`
  - Parse standard robots.txt
  - Parse with multiple User-Agents
  - Parse with wildcards
  - Parse with comments
  - Handle malformed files

- [ ] Test `RobotsTxtFetcher`
  - Fetch valid robots.txt
  - Handle 404 (not found)
  - Handle redirects
  - Handle timeouts
  - Handle network errors

- [ ] Test `RobotsTxtCache`
  - Cache storage and retrieval
  - TTL expiration
  - Thread safety
  - Cache invalidation

- [ ] Test rule matching
  - Path matching with wildcards
  - Longest match wins
  - User-Agent matching
  - Edge cases (empty rules, no rules)

#### 6.2 Integration Tests
**Files**: `tests/test_robots_integration.py`

- [ ] Test end-to-end flow
  - Check allowed URL
  - Check disallowed URL
  - Test with real robots.txt (mock HTTP)
  - Test cache behavior

#### 6.3 Scraper Integration Tests
**Files**: `tests/test_scraper.py`

- [ ] Test `get_price()` with robots.txt
  - Allowed URL proceeds
  - Disallowed URL raises error
  - Missing robots.txt allows scraping
  - Error handling

### Phase 7: Documentation

#### 7.1 Code Documentation
- [ ] Add docstrings to all classes and methods
- [ ] Add type hints
- [ ] Document edge cases

#### 7.2 User Documentation
**Files**: `docs/ROBOTS_TXT.md` (new)

- [ ] Document feature
- [ ] Explain configuration options
- [ ] Provide examples
- [ ] Troubleshooting guide

#### 7.3 Update README
**Files**: `README.md`

- [ ] Add robots.txt compliance to features
- [ ] Update configuration section

---

## 🔍 Technical Details

### Robots.txt Format Support

```python
# Supported directives:
User-agent: *
Disallow: /admin/
Disallow: /private/
Allow: /public/
Crawl-delay: 10

# Multiple User-Agent groups:
User-agent: Googlebot
Disallow: /search/

User-agent: *
Disallow: /
```

### Path Matching Algorithm

1. Extract path from URL (remove domain, query, fragment)
2. Normalize path (handle trailing slashes)
3. For each rule (in order):
   - Convert wildcards to regex pattern
   - Check if path matches rule pattern
   - Keep track of longest matching rule
4. Return result of longest matching rule
5. Default to allowed if no rules match

### Caching Strategy

- **Key**: Domain (e.g., "example.com")
- **Value**: Parsed rules dictionary
- **TTL**: 24 hours (configurable)
- **Invalidation**: Manual or on error (optional)
- **Thread Safety**: Use `threading.Lock` for cache operations

### Error Handling

| Scenario | Behavior |
|----------|----------|
| robots.txt not found (404) | Allow scraping (no robots.txt = allowed) |
| Network timeout | Allow scraping (fail open) or block (fail closed) - configurable |
| Malformed robots.txt | Log warning, allow scraping (fail open) |
| HTTP error (500, etc.) | Log error, allow scraping (fail open) |
| Disallowed by rules | Block scraping, raise exception |

---

## 🧪 Test Cases

### Unit Test Cases

1. **Parser Tests**
   - Parse simple robots.txt
   - Parse with multiple User-Agent groups
   - Parse with wildcards
   - Parse with comments and empty lines
   - Handle malformed syntax

2. **Fetcher Tests**
   - Fetch valid robots.txt
   - Handle 404 gracefully
   - Handle redirects (max 3)
   - Handle timeouts
   - Handle network errors

3. **Cache Tests**
   - Store and retrieve
   - TTL expiration
   - Thread safety (concurrent access)
   - Cache invalidation

4. **Rule Matching Tests**
   - Exact path match
   - Wildcard matching
   - Longest match wins
   - User-Agent matching
   - Default behavior (no rules)

### Integration Test Cases

1. **End-to-End Flow**
   - Allowed URL → scraping proceeds
   - Disallowed URL → exception raised
   - Missing robots.txt → scraping proceeds
   - Cached robots.txt → no fetch

2. **Error Scenarios**
   - Network timeout → configurable behavior
   - Malformed robots.txt → fail open
   - HTTP error → fail open

---

## 📊 Success Criteria

### Functional
- ✅ Robots.txt is checked before every scrape
- ✅ Disallowed URLs are blocked with clear error messages
- ✅ Allowed URLs proceed normally
- ✅ Missing robots.txt allows scraping
- ✅ Caching reduces redundant requests

### Performance
- ✅ Cache hit adds < 1ms overhead
- ✅ Cache miss adds < 2 seconds overhead
- ✅ No significant impact on existing scraping performance

### Quality
- ✅ 90%+ test coverage for robots.txt module
- ✅ All edge cases handled gracefully
- ✅ Clear error messages for users
- ✅ Comprehensive logging

---

## 🚀 Future Enhancements

### Phase 2 Features (Not in Initial Implementation)

1. **Crawl-Delay Enforcement**
   - Parse and respect crawl-delay directives
   - Add delays between requests
   - Per-domain delay tracking

2. **Sitemap.xml Support**
   - Parse sitemap.xml for allowed URLs
   - Use sitemap to optimize scraping

3. **User-Agent Rotation**
   - Support multiple User-Agent strings
   - Rotate based on domain

4. **Advanced Caching**
   - Persistent cache (Redis/file-based)
   - Cache warming for known domains
   - Cache statistics and monitoring

5. **Compliance Reporting**
   - Dashboard for robots.txt compliance
   - Historical compliance data
   - Alerting for violations

---

## 📚 References

- [RFC 9309 - Robots Exclusion Protocol](https://www.rfc-editor.org/rfc/rfc9309.html)
- [Google's Robots.txt Specification](https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt)
- [urllib.robotparser (Python stdlib)](https://docs.python.org/3/library/urllib.robotparser.html)

---

## ✅ Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Create `app/robots.py` module
- [ ] Implement `RobotsTxtFetcher`
- [ ] Implement `RobotsTxtParser`
- [ ] Create `Rule` dataclass
- [ ] Add `RobotsTxtDisallowedError` exception
- [ ] Add configuration options

### Phase 2: Caching
- [ ] Implement `RobotsTxtCache`
- [ ] Integrate cache with fetcher
- [ ] Add cache TTL support

### Phase 3: Rule Matching
- [ ] Implement path matching algorithm
- [ ] Implement User-Agent matching
- [ ] Implement `is_allowed()` method

### Phase 4: Integration
- [ ] Create `RobotsTxtChecker` class
- [ ] Integrate into `get_price()`
- [ ] Update error handling

### Phase 5: Logging & Monitoring
- [ ] Add comprehensive logging
- [ ] Add metrics (optional)

### Phase 6: Testing
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update scraper tests

### Phase 7: Documentation
- [ ] Add code documentation
- [ ] Create user documentation
- [ ] Update README

---

**Last Updated**: 2025-12-14  
**Status**: 📋 Ready for Implementation

