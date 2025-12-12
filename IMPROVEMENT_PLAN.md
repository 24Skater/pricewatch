# Pricewatch v2.0 → v2.1 Systematic Improvement Plan

> **AGENT DIRECTIVE**: This document is the single source of truth for all improvements. Execute each task sequentially within each phase. Do NOT skip tasks. Do NOT reorder tasks. Mark each checkbox upon completion. Do NOT proceed to the next phase until all tasks in the current phase are complete.

---

## 📋 Overview

| Attribute | Value |
|-----------|-------|
| **Current Version** | 2.0.0 |
| **Target Version** | 2.1.0 |
| **Total Phases** | 7 |
| **Total Tasks** | 47 |
| **Priority Order** | Security → Code Quality → Testing → DevOps → Documentation → UI/UX → Final |

---

## 🚦 Progress Tracker

| Phase | Name | Tasks | Status |
|-------|------|-------|--------|
| 1 | Security Hardening | 10 | ✅ Complete |
| 2 | Code Quality & DRY | 8 | ✅ Complete |
| 3 | Testing Improvements | 7 | ✅ Complete |
| 4 | DevOps & Infrastructure | 8 | ⬜ Not Started |
| 5 | Documentation | 6 | ⬜ Not Started |
| 6 | Performance & Modernization | 5 | ⬜ Not Started |
| 7 | Final Validation | 3 | ⬜ Not Started |

---

# Phase 1: Security Hardening 🔒

> **Priority**: CRITICAL  
> **Objective**: Eliminate all security vulnerabilities identified in code review

## Task 1.1: Fix Encryption Key Storage
**File**: `app/security.py`

- [x] **1.1.1** Remove file-based encryption key storage
- [x] **1.1.2** Add `ENCRYPTION_KEY` to `app/config.py` Settings class
- [x] **1.1.3** Modify `EncryptionService` to read key from environment variable
- [x] **1.1.4** Add fallback key generation ONLY for development environment with warning log
- [x] **1.1.5** Update `.env.example` with `ENCRYPTION_KEY` placeholder

**Acceptance Criteria**:
- ✅ `encryption.key` file is no longer created
- ✅ Key is read from `ENCRYPTION_KEY` environment variable
- ✅ Application fails to start in production if key is not set

---

## Task 1.2: Remove Duplicate SecurityError Class
**Files**: `app/security.py`, `app/exceptions.py`

- [x] **1.2.1** Remove `SecurityError` class from `app/security.py`
- [x] **1.2.2** Update import in `app/security.py` to use `from app.exceptions import SecurityError`
- [x] **1.2.3** Verify all files importing SecurityError use the correct source

**Acceptance Criteria**:
- ✅ Only ONE `SecurityError` class exists in `app/exceptions.py`
- ✅ All imports reference `app.exceptions.SecurityError`

---

## Task 1.3: Add CSRF Protection
**Files**: `app/main.py`, `app/templates/*.html`

- [x] **1.3.1** Create `app/csrf.py` with CSRF token generation and validation
- [x] **1.3.2** Add CSRF middleware to `app/main.py`
- [x] **1.3.3** Create Jinja2 global function for CSRF token insertion
- [x] **1.3.4** Update `base.html` to include CSRF meta tag
- [x] **1.3.5** Update ALL form templates to include CSRF hidden input:
  - [x] `index.html` (tracker create form)
  - [x] `tracker.html` (refresh form, selector form)
  - [x] `tracker_edit.html` (edit form, delete form)
  - [x] `admin/profiles.html` (delete forms)
  - [x] `admin/profile_form.html` (create/edit form)
- [x] **1.3.6** Add CSRF validation to ALL POST endpoints in `app/main.py`

**Acceptance Criteria**:
- ✅ All forms include `<input type="hidden" name="csrf_token" value="...">`
- ✅ POST requests without valid CSRF token return 403
- ✅ CSRF tokens are tied to user session

---

## Task 1.4: Add Security Headers Middleware
**File**: `app/main.py`

- [x] **1.4.1** Create security headers middleware class
- [x] **1.4.2** Add the following headers:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- [x] **1.4.3** Add Content-Security-Policy header (report-only mode initially)
- [x] **1.4.4** Register middleware in application startup

**Acceptance Criteria**:
- ✅ All responses include security headers
- ✅ Headers verified via `curl -I http://localhost:8000/`

---

## Task 1.5: Fix Rate Limiter Memory Leak
**File**: `app/security.py`

- [x] **1.5.1** Add `_last_cleanup` timestamp to `RateLimiter.__init__`
- [x] **1.5.2** Add `_cleanup_interval` constant (300 seconds)
- [x] **1.5.3** Implement `_cleanup_old_entries()` method to remove stale IPs
- [x] **1.5.4** Call cleanup in `is_allowed()` when interval exceeded
- [x] **1.5.5** Add maximum entries limit (10,000) with oldest-first eviction

**Acceptance Criteria**:
- ✅ Rate limiter memory usage stays bounded
- ✅ Old IP entries are automatically purged after window expiration

---

## Task 1.6: Expand SSRF Protection
**File**: `app/security.py`

- [x] **1.6.1** Create `is_private_ip()` function to check all private ranges:
  - `10.0.0.0/8`
  - `172.16.0.0/12`
  - `192.168.0.0/16`
  - `127.0.0.0/8`
  - `169.254.0.0/16` (link-local)
  - `::1` (IPv6 localhost)
  - `fc00::/7` (IPv6 private)
- [x] **1.6.2** Update `validate_url()` to use `is_private_ip()` in ALL environments
- [x] **1.6.3** Add URL scheme validation (only http/https)
- [x] **1.6.4** Block URLs with IP addresses in non-development environments

**Acceptance Criteria**:
- ✅ Private IP URLs are blocked in production/staging
- ✅ SSRF attempts are logged as security warnings

---

## Task 1.7: Secure Default Configuration
**File**: `app/config.py`

- [x] **1.7.1** Remove default value from `secret_key` field (kept default for dev, validated in production)
- [x] **1.7.2** Add validation to fail startup if `SECRET_KEY` not set in production
- [x] **1.7.3** Add `encryption_key` field with same validation
- [x] **1.7.4** Increase minimum `secret_key` length to 64 characters for production
- [x] **1.7.5** Add warning log if running in development mode

**Acceptance Criteria**:
- ✅ Application fails to start in production without required secrets
- ✅ Development mode shows clear warning in logs

---

## Task 1.8: Add Password/Secret Masking in Logs
**File**: `app/logging_config.py`

- [x] **1.8.1** Create `SensitiveDataFilter` logging filter class
- [x] **1.8.2** Define patterns to mask: passwords, tokens, keys, credentials
- [x] **1.8.3** Apply filter to all log handlers
- [x] **1.8.4** Test that sensitive data is masked in log output

**Acceptance Criteria**:
- ✅ Passwords and tokens appear as `***REDACTED***` in logs
- ✅ No sensitive data visible in `app.log`

---

## Task 1.9: Add Request ID Tracking
**Files**: `app/main.py`, `app/logging_config.py`

- [x] **1.9.1** Create middleware to generate UUID for each request
- [x] **1.9.2** Store request ID in context variable
- [x] **1.9.3** Include request ID in all log entries
- [x] **1.9.4** Return request ID in response header `X-Request-ID`

**Acceptance Criteria**:
- ✅ Each request has unique ID visible in logs
- ✅ Request ID can be used to trace full request lifecycle

---

## Task 1.10: Add Input Length Limits
**Files**: `app/schemas.py`, `app/main.py`

- [x] **1.10.1** Add `max_length` constraints to all Pydantic string fields:
  - URL: 2000 chars
  - Name: 500 chars
  - Selector: 1000 chars
  - Contact: 255 chars
- [x] **1.10.2** Add form field `maxlength` attributes to all HTML inputs
- [x] **1.10.3** Add server-side length validation before database operations

**Acceptance Criteria**:
- ✅ Oversized inputs are rejected with clear error message
- ✅ No truncation occurs silently

---

# Phase 2: Code Quality & DRY 🧹

> **Priority**: HIGH  
> **Objective**: Eliminate code duplication and improve maintainability

## Task 2.1: Extract Notification Service
**Files**: `app/services/notification_service.py` (new), `app/services/tracker_service.py`, `app/services/scheduler_service.py`

- [x] **2.1.1** Create new file `app/services/notification_service.py`
- [x] **2.1.2** Move `_send_price_notification()` logic to `NotificationService` class
- [x] **2.1.3** Add methods: `send_price_alert()`, `send_email()`, `send_sms()`
- [x] **2.1.4** Update `TrackerService` to use `NotificationService`
- [x] **2.1.5** Update `SchedulerService` to use `NotificationService`
- [x] **2.1.6** Remove duplicate notification methods from both services

**Acceptance Criteria**:
- ✅ Single source of truth for notification logic
- ✅ Both services delegate to `NotificationService`

---

## Task 2.2: Improve Module Exports
**Files**: `app/__init__.py`, `app/services/__init__.py`

- [x] **2.2.1** Update `app/__init__.py` with version and public exports:
  ```python
  __version__ = "2.1.0"
  __all__ = ["app", "settings", "get_db"]
  ```
- [x] **2.2.2** Update `app/services/__init__.py` with service exports:
  ```python
  __all__ = ["TrackerService", "ProfileService", "SchedulerService", "NotificationService"]
  ```
- [x] **2.2.3** Add `__all__` to `app/exceptions.py`
- [x] **2.2.4** Add `__all__` to `app/security.py`

**Acceptance Criteria**:
- ✅ All modules have explicit `__all__` exports
- ✅ `from app.services import TrackerService` works cleanly

---

## Task 2.3: Add Type Hints to Scraper
**File**: `app/scraper.py`

- [x] **2.3.1** Add type hints to all functions:
  - `fetch_html(url: str) -> str`
  - `fetch_html_js(url: str) -> str`
  - `_text(el: Tag) -> str`
  - `_nearby_text(el: Tag, limit_nodes: int = 3) -> str`
  - `_candidate_score(el: Tag, price_val: float, raw_text: str) -> int`
  - `smart_find_price(soup: BeautifulSoup) -> Optional[Tuple[float, str]]`
- [x] **2.3.2** Add return type hints to all parse functions
- [x] **2.3.3** Add type alias: `PriceResult = Tuple[Optional[float], str, Optional[str]]`
- [x] **2.3.4** Add docstrings to all public functions

**Acceptance Criteria**:
- ✅ `mypy app/scraper.py` passes with no errors
- ✅ All functions have docstrings

---

## Task 2.4: Fix Deprecated datetime.utcnow()
**Files**: `app/models.py`, any file using `datetime.utcnow()`

- [x] **2.4.1** Add import: `from datetime import datetime, timezone`
- [x] **2.4.2** Replace all `datetime.utcnow` with `lambda: datetime.now(timezone.utc)`
- [x] **2.4.3** Update any code comparing datetimes to use timezone-aware comparisons

**Acceptance Criteria**:
- ✅ No deprecation warnings for datetime usage
- ✅ All timestamps are timezone-aware UTC

---

## Task 2.5: Create Base Service Class
**File**: `app/services/base.py` (new)

- [x] **2.5.1** Create `BaseService` abstract class with:
  - `__init__(self, db: Session)`
  - `_commit()` helper with error handling
  - `_rollback()` helper
  - Common logging setup
- [x] **2.5.2** Update `TrackerService` to inherit from `BaseService`
- [x] **2.5.3** Update `ProfileService` to inherit from `BaseService`
- [x] **2.5.4** Update `SchedulerService` to inherit from `BaseService`

**Acceptance Criteria**:
- ✅ Common database operations handled by base class
- ✅ Reduced boilerplate in service classes

---

## Task 2.6: Consolidate Configuration Access
**File**: `app/scraper.py`

- [x] **2.6.1** Remove direct `os.getenv()` calls from `scraper.py`
- [x] **2.6.2** Use `settings.use_js_fallback` instead of `USE_JS` constant
- [x] **2.6.3** Use `settings.request_timeout` instead of hardcoded `30`
- [x] **2.6.4** Remove module-level constants that duplicate config

**Acceptance Criteria**:
- ✅ All configuration accessed via `settings` object
- ✅ No `os.getenv()` calls outside `config.py`

---

## Task 2.7: Improve Error Messages
**Files**: `app/exceptions.py`, all service files

- [x] **2.7.1** Add `code` field to all exception classes for machine-readable errors
- [x] **2.7.2** Add `details` field for additional context
- [x] **2.7.3** Create exception handler in `main.py` for consistent JSON error responses
- [x] **2.7.4** Update all `raise` statements to include meaningful messages

**Acceptance Criteria**:
- ✅ All API errors return structured JSON: `{"error": "...", "code": "...", "details": {...}}`
- ✅ Error messages are user-friendly

---

## Task 2.8: Remove Duplicate Test File
**File**: `tests/test_price_regex.py`

- [x] **2.8.1** Delete `tests/test_price_regex.py` (duplicate of `test_price_parsing.py`)
- [x] **2.8.2** Ensure `tests/test_price_parsing.py` has comprehensive regex tests
- [x] **2.8.3** Add edge case tests to `test_price_parsing.py`:
  - Currency symbols (€, £, ¥)
  - Negative prices (error case)
  - Prices with spaces

**Acceptance Criteria**:
- ✅ No duplicate test files
- ✅ Price parsing has comprehensive test coverage

---

# Phase 3: Testing Improvements 🧪

> **Priority**: HIGH  
> **Objective**: Achieve 80%+ test coverage with meaningful tests

## Task 3.1: Add Scraper Unit Tests
**File**: `tests/test_scraper.py` (new)

- [x] **3.1.1** Create test file with fixtures for HTML samples
- [x] **3.1.2** Test `parse_price_from_jsonld()` with valid/invalid JSON-LD
- [x] **3.1.3** Test `parse_price_from_meta()` with various meta tag formats
- [x] **3.1.4** Test `smart_find_price()` with complex HTML
- [x] **3.1.5** Test `extract_title()` with various title formats
- [x] **3.1.6** Test `_candidate_score()` scoring logic
- [x] **3.1.7** Mock `requests.get()` to avoid network calls in tests

**Acceptance Criteria**:
- ✅ Scraper module has 90%+ test coverage
- ✅ All tests pass without network access

---

## Task 3.2: Add Notification Tests
**File**: `tests/test_notifications.py` (new)

- [x] **3.2.1** Create test file with SMTP/Twilio mocks
- [x] **3.2.2** Test `send_email()` with valid configuration
- [x] **3.2.3** Test `send_email()` with missing SMTP config (skip behavior)
- [x] **3.2.4** Test `send_sms()` with valid configuration
- [x] **3.2.5** Test `send_sms()` with missing Twilio config (skip behavior)
- [x] **3.2.6** Test credential decryption in notification flow

**Acceptance Criteria**:
- ✅ Notification sending is fully tested with mocks
- ✅ No actual emails/SMS sent during tests

---

## Task 3.3: Add Integration Tests
**File**: `tests/test_integration.py` (new)

- [x] **3.3.1** Test full tracker creation flow (form → database → response)
- [x] **3.3.2** Test price refresh flow with mocked scraper
- [x] **3.3.3** Test profile creation with encrypted storage
- [x] **3.3.4** Test scheduler polling with mocked scraper
- [x] **3.3.5** Test rate limiting behavior (exceed limit → 429)

**Acceptance Criteria**:
- ✅ End-to-end flows tested
- ✅ All tests use test database (not production)

---

## Task 3.4: Add Security Tests
**File**: `tests/test_security.py` (update existing)

- [x] **3.4.1** Add CSRF protection tests
- [x] **3.4.2** Add SSRF protection tests (private IP blocking)
- [x] **3.4.3** Add rate limiter cleanup tests
- [x] **3.4.4** Add input length validation tests
- [x] **3.4.5** Add XSS sanitization tests with malicious payloads

**Acceptance Criteria**:
- ✅ Security features have explicit test coverage
- ✅ Attack vectors are tested and blocked

---

## Task 3.5: Add Monitoring Tests
**File**: `tests/test_monitoring.py` (new)

- [x] **3.5.1** Test `HealthChecker.check_database()` success/failure
- [x] **3.5.2** Test `HealthChecker.check_system_resources()`
- [x] **3.5.3** Test `HealthChecker.comprehensive_health_check()` overall status
- [x] **3.5.4** Test health endpoints return correct structure

**Acceptance Criteria**:
- ✅ Monitoring functionality fully tested
- ✅ Health check failures handled gracefully

---

## Task 3.6: Add Test Coverage Configuration
**Files**: `pyproject.toml` or `setup.cfg`, `.coveragerc`

- [x] **3.6.1** Create `.coveragerc` with coverage settings:
  ```ini
  [run]
  source = app
  omit = app/__init__.py, */tests/*
  
  [report]
  fail_under = 80
  show_missing = true
  ```
- [x] **3.6.2** Add coverage badge generation
- [x] **3.6.3** Document coverage requirements in README

**Acceptance Criteria**:
- ✅ `pytest --cov=app --cov-fail-under=80` passes
- ✅ Coverage report generated

---

## Task 3.7: Add Test Fixtures for Common Scenarios
**File**: `tests/conftest.py` (update)

- [x] **3.7.1** Add fixture for authenticated session (future use)
- [x] **3.7.2** Add fixture for tracker with price history
- [x] **3.7.3** Add fixture for profile with encrypted credentials
- [x] **3.7.4** Add fixture for mock scraper responses
- [x] **3.7.5** Add fixture for mock SMTP server

**Acceptance Criteria**:
- ✅ Common test scenarios easily reusable
- ✅ Tests are DRY and readable

---

# Phase 4: DevOps & Infrastructure 🚀

> **Priority**: MEDIUM  
> **Objective**: Production-ready deployment configuration

## Task 4.1: Create .gitignore
**File**: `.gitignore` (new)

- [ ] **4.1.1** Create comprehensive `.gitignore`:
  ```gitignore
  # Python
  __pycache__/
  *.py[cod]
  *$py.class
  *.so
  .Python
  build/
  dist/
  eggs/
  *.egg-info/
  .venv/
  venv/
  ENV/
  
  # Environment
  .env
  .env.local
  .env.*.local
  
  # Secrets
  encryption.key
  *.pem
  *.key
  
  # Database
  *.db
  *.sqlite3
  
  # Logs
  *.log
  logs/
  
  # IDE
  .idea/
  .vscode/
  *.swp
  *.swo
  
  # Testing
  .coverage
  htmlcov/
  .pytest_cache/
  .tox/
  
  # OS
  .DS_Store
  Thumbs.db
  ```

**Acceptance Criteria**:
- Sensitive files not tracked
- Clean repository state

---

## Task 4.2: Create .env.example
**File**: `.env.example` (new)

- [ ] **4.2.1** Create template with all environment variables:
  ```env
  # Application
  SECRET_KEY=generate-a-64-character-random-string-here
  ENCRYPTION_KEY=generate-a-fernet-key-here
  ENVIRONMENT=development
  DEBUG=false
  
  # Database
  DATABASE_URL=sqlite:///pricewatch.db
  
  # Rate Limiting
  RATE_LIMIT_PER_MINUTE=60
  RATE_LIMIT_BURST=10
  
  # Scraping
  REQUEST_TIMEOUT=30
  MAX_RETRIES=3
  USE_JS_FALLBACK=false
  SCHEDULE_MINUTES=30
  
  # Logging
  LOG_LEVEL=INFO
  LOG_FORMAT=json
  
  # SMTP (Optional)
  SMTP_HOST=
  SMTP_PORT=587
  SMTP_USER=
  SMTP_PASS=
  FROM_EMAIL=
  
  # Twilio (Optional)
  TWILIO_ACCOUNT_SID=
  TWILIO_AUTH_TOKEN=
  TWILIO_FROM_NUMBER=
  ```
- [ ] **4.2.2** Add comments explaining each variable
- [ ] **4.2.3** Add instructions for generating secrets

**Acceptance Criteria**:
- New developers can copy and configure easily
- All variables documented

---

## Task 4.3: Improve Dockerfile
**File**: `Dockerfile`

- [ ] **4.3.1** Implement multi-stage build:
  ```dockerfile
  # Build stage
  FROM python:3.12-slim as builder
  ...
  
  # Production stage
  FROM python:3.12-slim as production
  ...
  ```
- [ ] **4.3.2** Create non-root user `appuser`
- [ ] **4.3.3** Add health check:
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
  ```
- [ ] **4.3.4** Optimize layer caching
- [ ] **4.3.5** Add labels for image metadata

**Acceptance Criteria**:
- Image size reduced by 50%+
- Container runs as non-root
- Health check works

---

## Task 4.4: Create .dockerignore
**File**: `.dockerignore` (new)

- [ ] **4.4.1** Create `.dockerignore`:
  ```
  .git
  .gitignore
  .env
  .env.*
  *.md
  !README.md
  tests/
  __pycache__/
  *.pyc
  *.pyo
  .venv/
  venv/
  .coverage
  htmlcov/
  *.db
  *.log
  .idea/
  .vscode/
  ```

**Acceptance Criteria**:
- Unnecessary files excluded from Docker context
- Build time reduced

---

## Task 4.5: Improve docker-compose.yml
**File**: `docker-compose.yml`

- [ ] **4.5.1** Add health check configuration
- [ ] **4.5.2** Add resource limits
- [ ] **4.5.3** Add logging configuration
- [ ] **4.5.4** Add volume for persistent database
- [ ] **4.5.5** Add restart policy
- [ ] **4.5.6** Create `docker-compose.prod.yml` for production overrides

**Acceptance Criteria**:
- Production-ready compose configuration
- Data persists across restarts

---

## Task 4.6: Add GitHub Actions CI
**File**: `.github/workflows/ci.yml` (new)

- [ ] **4.6.1** Create workflow file with:
  ```yaml
  name: CI
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
        - run: pip install -r requirements.txt
        - run: pytest --cov=app --cov-fail-under=80
    
    lint:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
        - run: pip install ruff mypy
        - run: ruff check app/
        - run: mypy app/
    
    security:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - run: pip install bandit safety
        - run: bandit -r app/
        - run: safety check
  ```
- [ ] **4.6.2** Add status badge to README

**Acceptance Criteria**:
- CI runs on every push/PR
- Tests, linting, security checks automated

---

## Task 4.7: Add Pre-commit Configuration
**File**: `.pre-commit-config.yaml` (new)

- [ ] **4.7.1** Create pre-commit config:
  ```yaml
  repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.1.6
      hooks:
        - id: ruff
          args: [--fix]
        - id: ruff-format
    
    - repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v4.5.0
      hooks:
        - id: trailing-whitespace
        - id: end-of-file-fixer
        - id: check-yaml
        - id: check-added-large-files
        - id: detect-private-key
    
    - repo: https://github.com/pre-commit/mirrors-mypy
      rev: v1.7.1
      hooks:
        - id: mypy
          additional_dependencies: [pydantic, sqlalchemy]
  ```
- [ ] **4.7.2** Add install instructions to README
- [ ] **4.7.3** Run pre-commit on all files to fix existing issues

**Acceptance Criteria**:
- Pre-commit hooks catch issues before commit
- All existing code passes pre-commit

---

## Task 4.8: Add pyproject.toml
**File**: `pyproject.toml` (new)

- [ ] **4.8.1** Create modern Python project configuration:
  ```toml
  [project]
  name = "pricewatch"
  version = "2.1.0"
  description = "Enterprise price tracking application"
  requires-python = ">=3.10"
  
  [tool.ruff]
  line-length = 100
  target-version = "py310"
  select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
  
  [tool.mypy]
  python_version = "3.10"
  strict = true
  
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  asyncio_mode = "auto"
  ```
- [ ] **4.8.2** Configure all tools via pyproject.toml
- [ ] **4.8.3** Remove any redundant config files

**Acceptance Criteria**:
- Single source of project configuration
- Modern Python packaging standards

---

# Phase 5: Documentation 📚

> **Priority**: MEDIUM  
> **Objective**: Complete documentation for open source readiness

## Task 5.1: Create CONTRIBUTING.md
**File**: `CONTRIBUTING.md` (new)

- [ ] **5.1.1** Write contribution guidelines including:
  - How to set up development environment
  - Code style guidelines
  - How to run tests
  - How to submit pull requests
  - Commit message format
- [ ] **5.1.2** Add issue/PR templates reference

**Acceptance Criteria**:
- New contributors can onboard easily
- Clear expectations set

---

## Task 5.2: Create CODE_OF_CONDUCT.md
**File**: `CODE_OF_CONDUCT.md` (new)

- [ ] **5.2.1** Adopt Contributor Covenant v2.1
- [ ] **5.2.2** Add enforcement contact information

**Acceptance Criteria**:
- Community standards documented
- Enforcement process clear

---

## Task 5.3: Create SECURITY.md
**File**: `SECURITY.md` (new)

- [ ] **5.3.1** Write security policy including:
  - Supported versions
  - How to report vulnerabilities
  - Expected response time
  - Disclosure policy
- [ ] **5.3.2** Add security contact email

**Acceptance Criteria**:
- Security researchers know how to report issues
- Responsible disclosure process documented

---

## Task 5.4: Create GitHub Issue Templates
**Files**: `.github/ISSUE_TEMPLATE/*.yml` (new)

- [ ] **5.4.1** Create bug report template
- [ ] **5.4.2** Create feature request template
- [ ] **5.4.3** Create question template
- [ ] **5.4.4** Create config.yml to configure template chooser

**Acceptance Criteria**:
- Issues have consistent structure
- Required information collected

---

## Task 5.5: Create Pull Request Template
**File**: `.github/PULL_REQUEST_TEMPLATE.md` (new)

- [ ] **5.5.1** Create PR template with:
  - Description section
  - Type of change checkboxes
  - Testing checklist
  - Documentation checklist

**Acceptance Criteria**:
- PRs have consistent structure
- Review process streamlined

---

## Task 5.6: Update README.md
**File**: `README.md`

- [ ] **5.6.1** Add badges (CI status, coverage, license, Python version)
- [ ] **5.6.2** Add table of contents
- [ ] **5.6.3** Add architecture diagram (ASCII or link to image)
- [ ] **5.6.4** Update version references to 2.1.0
- [ ] **5.6.5** Add "Built With" section listing technologies
- [ ] **5.6.6** Add acknowledgments section

**Acceptance Criteria**:
- README is visually appealing
- All information current

---

# Phase 6: Performance & Modernization ⚡

> **Priority**: LOW  
> **Objective**: Modern async patterns and performance improvements

## Task 6.1: Add Async HTTP Client
**File**: `app/scraper.py`, `requirements.txt`

- [ ] **6.1.1** Add `httpx` to requirements.txt
- [ ] **6.1.2** Create async version of `fetch_html()`:
  ```python
  async def fetch_html_async(url: str) -> str:
      async with httpx.AsyncClient() as client:
          response = await client.get(url, headers=HEADERS, timeout=30)
          response.raise_for_status()
          return response.text
  ```
- [ ] **6.1.3** Keep sync version for background scheduler compatibility
- [ ] **6.1.4** Add configuration flag to choose sync/async mode

**Acceptance Criteria**:
- API endpoints don't block event loop
- Background jobs still work synchronously

---

## Task 6.2: Add Database Connection Pooling Config
**File**: `app/database.py`, `app/config.py`

- [ ] **6.2.1** Add pool configuration to Settings:
  ```python
  db_pool_size: int = 5
  db_max_overflow: int = 10
  db_pool_timeout: int = 30
  ```
- [ ] **6.2.2** Configure SQLAlchemy engine with pool settings for PostgreSQL
- [ ] **6.2.3** Keep StaticPool for SQLite development

**Acceptance Criteria**:
- Database connections properly pooled
- Configuration documented

---

## Task 6.3: Add Response Caching Headers
**File**: `app/main.py`

- [ ] **6.3.1** Add `Cache-Control` headers to static responses
- [ ] **6.3.2** Add `ETag` support for tracker detail pages
- [ ] **6.3.3** Add `no-cache` for sensitive endpoints (admin, health)

**Acceptance Criteria**:
- Static assets cacheable
- Dynamic content not cached inappropriately

---

## Task 6.4: Optimize Database Queries
**Files**: `app/services/*.py`, `app/monitoring.py`

- [ ] **6.4.1** Add `joinedload` for tracker→profile relationship
- [ ] **6.4.2** Add pagination to `get_all_trackers()` method
- [ ] **6.4.3** Add query timeout configuration
- [ ] **6.4.4** Add query count logging in debug mode

**Acceptance Criteria**:
- N+1 queries eliminated
- Large datasets handled efficiently

---

## Task 6.5: Add Prometheus Metrics
**Files**: `app/monitoring.py`, `app/main.py`

- [ ] **6.5.1** Add prometheus_client metrics:
  - `pricewatch_requests_total` (counter)
  - `pricewatch_request_duration_seconds` (histogram)
  - `pricewatch_trackers_total` (gauge)
  - `pricewatch_scrape_errors_total` (counter)
- [ ] **6.5.2** Add `/metrics` endpoint returning Prometheus format
- [ ] **6.5.3** Add middleware for request metrics collection

**Acceptance Criteria**:
- Prometheus can scrape metrics
- Key application metrics exposed

---

# Phase 7: Final Validation ✅

> **Priority**: CRITICAL  
> **Objective**: Ensure all improvements work together

## Task 7.1: Full Test Suite Execution
**Command**: `pytest tests/ -v --cov=app --cov-report=html`

- [ ] **7.1.1** Run complete test suite
- [ ] **7.1.2** Verify 80%+ coverage achieved
- [ ] **7.1.3** Fix any failing tests
- [ ] **7.1.4** Review coverage report for gaps

**Acceptance Criteria**:
- All tests pass
- Coverage ≥ 80%

---

## Task 7.2: Security Audit
**Commands**: Various security tools

- [ ] **7.2.1** Run `bandit -r app/` - fix all high/medium issues
- [ ] **7.2.2** Run `safety check` - update vulnerable dependencies
- [ ] **7.2.3** Run `pip-audit` - check for known vulnerabilities
- [ ] **7.2.4** Manual review of authentication/authorization flows
- [ ] **7.2.5** Test CSRF protection manually
- [ ] **7.2.6** Test rate limiting manually

**Acceptance Criteria**:
- Zero high/medium security issues
- All dependencies up-to-date

---

## Task 7.3: Update Version and Release
**Files**: Various

- [ ] **7.3.1** Update version to `2.1.0` in:
  - `app/__init__.py`
  - `pyproject.toml`
  - `app/main.py` (FastAPI app version)
  - `app/monitoring.py` (health check version)
- [ ] **7.3.2** Update `CHANGELOG.md` with all changes
- [ ] **7.3.3** Create git tag `v2.1.0`
- [ ] **7.3.4** Final README review

**Acceptance Criteria**:
- Version consistent everywhere
- Changelog complete
- Ready for release

---

# 📝 Agent Execution Rules

1. **Sequential Execution**: Complete tasks in order within each phase
2. **No Skipping**: Every checkbox must be addressed
3. **Atomic Commits**: Commit after each major task (e.g., 1.1, 1.2, etc.)
4. **Testing**: Run `pytest` after each phase to ensure no regressions
5. **Documentation**: Update docs as code changes
6. **Mark Progress**: Update checkboxes in this file as tasks complete
7. **Blockers**: If blocked, document reason and continue to next task within same phase

---

# 🔄 Status Updates

## Current Phase: 4 (DevOps & Infrastructure)
## Current Task: 4.1 (Create .gitignore)
## Last Updated: 2025-12-12
## Blockers: None

### Phase 3 Complete! ✅ (7/7 tasks)
- ✅ Task 3.1: Add Scraper Unit Tests (7/7 subtasks complete)
- ✅ Task 3.2: Add Notification Tests (6/6 subtasks complete)
- ✅ Task 3.3: Add Integration Tests (5/5 subtasks complete)
- ✅ Task 3.4: Add Security Tests (5/5 subtasks complete)
- ✅ Task 3.5: Add Monitoring Tests (4/4 subtasks complete)
- ✅ Task 3.6: Add Test Coverage Configuration (3/3 subtasks complete)
- ✅ Task 3.7: Add Test Fixtures for Common Scenarios (5/5 subtasks complete)

### Phase 2 Complete! ✅ (8/8 tasks)
- ✅ Task 2.1: Extract Notification Service (6/6 subtasks complete)
- ✅ Task 2.2: Improve Module Exports (4/4 subtasks complete)
- ✅ Task 2.3: Add Type Hints to Scraper (4/4 subtasks complete)
- ✅ Task 2.4: Fix Deprecated datetime.utcnow() (3/3 subtasks complete)
- ✅ Task 2.5: Create Base Service Class (4/4 subtasks complete)
- ✅ Task 2.6: Consolidate Configuration Access (4/4 subtasks complete)
- ✅ Task 2.7: Improve Error Messages (4/4 subtasks complete)
- ✅ Task 2.8: Remove Duplicate Test File (3/3 subtasks complete)

### Phase 1 Complete! ✅ (10/10 tasks)
- ✅ Task 1.1: Fix Encryption Key Storage (5/5 subtasks complete)
- ✅ Task 1.2: Remove Duplicate SecurityError Class (3/3 subtasks complete)
- ✅ Task 1.3: Add CSRF Protection (6/6 subtasks complete)
- ✅ Task 1.4: Add Security Headers Middleware (4/4 subtasks complete)
- ✅ Task 1.5: Fix Rate Limiter Memory Leak (5/5 subtasks complete)
- ✅ Task 1.6: Expand SSRF Protection (4/4 subtasks complete)
- ✅ Task 1.7: Secure Default Configuration (5/5 subtasks complete)
- ✅ Task 1.8: Add Password/Secret Masking in Logs (4/4 subtasks complete)
- ✅ Task 1.9: Add Request ID Tracking (4/4 subtasks complete)
- ✅ Task 1.10: Add Input Length Limits (3/3 subtasks complete)

---

*This document is the authoritative guide for the Pricewatch v2.1 improvement project.*

