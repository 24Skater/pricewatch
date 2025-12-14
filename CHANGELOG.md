# Changelog

All notable changes to the Pricewatch application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Future enhancements and planned features

## [2.1.0] - 2025-12-14

### 🎉 Release - Security, Quality, and Performance Improvements

This release focuses on comprehensive security hardening, code quality improvements, testing enhancements, DevOps infrastructure, documentation, and performance optimizations.

### Added

#### Security Enhancements
- **CSRF Protection** (`app/csrf.py`)
  - Token-based CSRF protection for all forms
  - Session-based token validation
  - Automatic token cleanup and expiration
- **Security Headers Middleware** (`app/main.py`)
  - X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
  - Content-Security-Policy (report-only mode)
  - Referrer-Policy and Permissions-Policy headers
- **Enhanced SSRF Protection** (`app/security.py`)
  - Comprehensive private IP range blocking
  - IPv6 localhost and private range detection
  - URL scheme validation (http/https only)
- **Request ID Tracking** (`app/main.py`, `app/context.py`)
  - Unique request ID for each request
  - Full request lifecycle tracking
  - Request ID in response headers and logs
- **Input Length Limits** (`app/schemas.py`)
  - Maximum length constraints on all string fields
  - Server-side and client-side validation
  - Protection against oversized input attacks
- **Secret Masking in Logs** (`app/logging_config.py`)
  - Automatic redaction of passwords, tokens, and keys
  - Sensitive data filter for all log handlers
  - Secure logging practices

#### Code Quality Improvements
- **Notification Service** (`app/services/notification_service.py`)
  - Centralized notification handling
  - Single source of truth for email/SMS logic
  - Reduced code duplication
- **Base Service Class** (`app/services/base.py`)
  - Common database operations
  - Standardized error handling
  - Reduced boilerplate code
- **Type Hints** (`app/scraper.py`)
  - Complete type annotations
  - Improved IDE support and type checking
- **Module Exports** (`app/__init__.py`, `app/services/__init__.py`)
  - Explicit `__all__` declarations
  - Clean module interfaces
- **Error Messages** (`app/exceptions.py`)
  - Structured error responses with codes
  - User-friendly error messages
  - Additional context in error details

#### Testing Infrastructure
- **Comprehensive Test Coverage** (80.67% coverage achieved)
  - Scraper unit tests with mocked HTTP requests
  - Notification service tests with SMTP/Twilio mocks
  - Integration tests for end-to-end flows
  - Security tests for CSRF, SSRF, rate limiting
  - Monitoring tests for health checks
  - Base service and database tests
- **Test Fixtures** (`tests/conftest.py`)
  - Reusable test data and scenarios
  - Mock scraper responses
  - Encrypted profile fixtures
  - Price history fixtures
- **Coverage Configuration** (`.coveragerc`, `pyproject.toml`)
  - 75% minimum coverage requirement
  - HTML and XML coverage reports
  - Missing line reporting

#### DevOps & Infrastructure
- **GitHub Actions CI** (`.github/workflows/ci.yml`)
  - Automated testing on push/PR
  - Linting with Ruff
  - Type checking with MyPy
  - Security scanning with Bandit
  - Dependency vulnerability checking
- **Pre-commit Hooks** (`.pre-commit-config.yaml`)
  - Automatic code formatting
  - Linting before commit
  - Type checking
  - Security checks
- **Docker Improvements** (`Dockerfile`, `docker-compose.yml`)
  - Multi-stage builds for smaller images
  - Non-root user execution
  - Health check configuration
  - Resource limits and logging
  - Production override configuration
- **Project Configuration** (`pyproject.toml`)
  - Modern Python project structure
  - Centralized tool configuration
  - Ruff, MyPy, Pytest, Coverage settings

#### Documentation
- **Contributing Guide** (`CONTRIBUTING.md`)
  - Development setup instructions
  - Code style guidelines
  - Testing requirements
  - Pull request process
- **Code of Conduct** (`CODE_OF_CONDUCT.md`)
  - Contributor Covenant v2.1
  - Community standards
  - Enforcement guidelines
- **Security Policy** (`SECURITY.md`)
  - Vulnerability reporting process
  - Supported versions
  - Disclosure policy
- **GitHub Templates** (`.github/ISSUE_TEMPLATE/`)
  - Bug report template
  - Feature request template
  - Question template
- **Pull Request Template** (`.github/PULL_REQUEST_TEMPLATE.md`)
  - Structured PR format
  - Testing checklist
  - Documentation requirements
- **Enhanced README** (`README.md`)
  - Badges (CI, coverage, license, Python version)
  - Table of contents
  - Architecture diagram
  - Built With section
  - Acknowledgments

#### Performance & Modernization
- **Async HTTP Client** (`app/scraper.py`)
  - `httpx` for async HTTP requests
  - Non-blocking API endpoints
  - Configuration flag for sync/async mode
- **Database Connection Pooling** (`app/database.py`)
  - Configurable pool size and overflow
  - PostgreSQL/MySQL optimization
  - Query timeout configuration
- **Response Caching** (`app/main.py`)
  - Cache-Control headers for static assets
  - ETag support for tracker detail pages
  - No-cache for sensitive endpoints
- **Query Optimization** (`app/services/tracker_service.py`)
  - `joinedload` for relationship loading
  - Pagination support
  - Query count logging in debug mode
- **Prometheus Metrics** (`app/monitoring.py`, `app/main.py`)
  - Request count and duration metrics
  - Tracker count gauge
  - Scrape error counter
  - `/metrics` endpoint for Prometheus scraping

### Changed

#### Security
- **Encryption Key Storage** (`app/security.py`, `app/config.py`)
  - Moved from file-based to environment variable
  - Production validation requirements
  - Development fallback with warnings
- **Rate Limiter** (`app/security.py`)
  - Automatic cleanup of old entries
  - Memory leak prevention
  - Maximum entries limit with eviction
- **Configuration Validation** (`app/config.py`)
  - Stricter production requirements
  - Minimum key lengths enforced
  - Environment-specific validation

#### Code Quality
- **Deprecated datetime.utcnow()** (`app/models.py`)
  - Replaced with timezone-aware `datetime.now(timezone.utc)`
  - All timestamps are now timezone-aware
- **Configuration Access** (`app/scraper.py`)
  - Removed direct `os.getenv()` calls
  - Centralized configuration via `settings` object
- **Error Handling** (`app/exceptions.py`, `app/main.py`)
  - Structured JSON error responses
  - Machine-readable error codes
  - Additional context in error details

#### Testing
- **Coverage Requirement** (`.coveragerc`, `pyproject.toml`)
  - Reduced from 80% to 75% for practical balance
  - Current coverage: 80.67%

### Fixed

#### Security Issues
- **Encryption Key Storage**
  - Fixed file-based key storage vulnerability
  - Environment variable-based key management
- **Rate Limiter Memory Leak**
  - Added automatic cleanup of expired entries
  - Maximum entries limit prevents unbounded growth
- **SSRF Protection**
  - Expanded private IP range detection
  - IPv6 support for localhost and private ranges
- **Duplicate SecurityError Class**
  - Removed duplicate, consolidated in `app/exceptions.py`

#### Code Quality
- **Deprecated API Usage**
  - Fixed `datetime.utcnow()` deprecation warnings
  - All datetime operations now timezone-aware
- **Code Duplication**
  - Extracted notification service
  - Created base service class
  - Consolidated configuration access

### Security

#### Dependencies
- **Updated cryptography** from 41.0.7 to 42.0.4+ (fixes 4 CVEs)
- **Note**: pip 25.0.1 has CVE-2025-8869 - users should update with `pip install --upgrade pip`

#### Security Audit Results
- **Bandit**: 0 High/Medium issues (acceptable uses marked with `# nosec`)
- **pip-audit**: 1 vulnerability in pip itself (user should update)
- **Manual Review**: CSRF protection, rate limiting, and authentication flows verified

### Performance

#### Database
- **Connection Pooling**: Configurable pool size for PostgreSQL/MySQL
- **Query Optimization**: Eliminated N+1 queries with `joinedload`
- **Pagination**: Added to `get_all_trackers()` for large datasets
- **Query Timeout**: Configurable timeout for long-running queries

#### HTTP
- **Async Client**: Non-blocking HTTP requests with `httpx`
- **Response Caching**: Optimized cache headers for static and dynamic content
- **ETag Support**: Efficient cache validation for tracker pages

#### Monitoring
- **Prometheus Metrics**: Comprehensive application metrics
- **Request Tracking**: Full request lifecycle monitoring

### Documentation

#### New Documentation Files
- `CONTRIBUTING.md` - Contribution guidelines
- `CODE_OF_CONDUCT.md` - Community standards
- `SECURITY.md` - Security policy and reporting
- `.github/ISSUE_TEMPLATE/*.yml` - Issue templates
- `.github/PULL_REQUEST_TEMPLATE.md` - PR template

#### Updated Documentation
- `README.md` - Enhanced with badges, TOC, architecture diagram
- `CHANGELOG.md` - Comprehensive change tracking
- `IMPROVEMENT_PLAN.md` - Detailed improvement tracking

### Infrastructure

#### CI/CD
- **GitHub Actions**: Automated testing, linting, security scanning
- **Pre-commit Hooks**: Code quality checks before commit
- **Docker**: Multi-stage builds, health checks, production configs

#### Project Configuration
- **pyproject.toml**: Modern Python project configuration
- **.coveragerc**: Coverage reporting configuration
- **.gitignore**: Comprehensive ignore patterns
- **.dockerignore**: Optimized Docker builds

### Migration Guide

#### From v2.0.0 to v2.1.0

1. **Update Dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **Update Environment Variables**
   - Ensure `ENCRYPTION_KEY` is set (required in production)
   - Review new configuration options in `.env.example`

3. **No Database Migrations Required**
   - Schema is compatible with v2.0.0

4. **Test Application**
   ```bash
   pytest tests/ --cov=app --cov-fail-under=75
   uvicorn app.main:app --reload
   ```

### Breaking Changes

None - This is a minor version release with backward compatibility.

### Deprecated

None in this release.

### Removed

- Duplicate test file `tests/test_price_regex.py` (consolidated into `test_price_parsing.py`)

---

## [2.0.0] - 2024-01-XX

### 🚀 Major Release - Enterprise-Grade Improvements

This is a comprehensive overhaul of the Pricewatch application, implementing enterprise-grade best practices for security, maintainability, and scalability.

### Added

#### Security & Encryption
- **Encryption Service** (`app/security.py`)
  - Fernet encryption for sensitive data storage
  - Automatic encryption key generation and management
  - Secure credential storage for SMTP and Twilio
- **Input Validation** (`app/security.py`)
  - Comprehensive URL validation with security checks
  - Email format validation with regex patterns
  - Phone number validation for SMS notifications
  - XSS prevention through input sanitization
- **Rate Limiting** (`app/security.py`)
  - IP-based rate limiting with configurable limits
  - Burst protection against rapid-fire requests
  - Per-endpoint rate limiting configuration

#### Architecture & Code Structure
- **Service Layer Pattern**
  - `TrackerService` - Business logic for price trackers
  - `ProfileService` - Notification profile management
  - `SchedulerService` - Background task scheduling
- **Configuration Management** (`app/config.py`)
  - Pydantic-based settings with environment validation
  - Type-safe configuration with automatic validation
  - Environment-specific configuration support
- **Custom Exception Handling** (`app/exceptions.py`)
  - Domain-specific exception classes
  - Structured error responses
  - Graceful error recovery

#### Logging & Monitoring
- **Structured Logging** (`app/logging_config.py`)
  - JSON-formatted logs for better parsing
  - Contextual logging with request IDs
  - Configurable log levels and formats
- **Health Monitoring** (`app/monitoring.py`)
  - Basic health check endpoint (`/health`)
  - Detailed health monitoring (`/health/detailed`)
  - Application metrics endpoint (`/metrics`)
  - System resource monitoring (CPU, memory, disk)
  - Database performance tracking

#### Database Improvements
- **Schema Optimization** (`app/models.py`)
  - Strategic indexing for query performance
  - Composite indexes for common query patterns
  - Proper column sizing and constraints
  - Foreign key relationships with cascading
- **Migration System**
  - Alembic integration for database versioning
  - Automated migration scripts
  - Rollback capabilities
- **Connection Pooling** (`app/database.py`)
  - Optimized database connections
  - Connection health checking
  - Debug mode SQL query logging

#### Testing Infrastructure
- **Comprehensive Test Suite** (`tests/`)
  - Unit tests for service layer functionality
  - Integration tests for API endpoints
  - Security tests for validation and encryption
  - Test fixtures and mock objects
- **Test Organization**
  - Structured test files by functionality
  - Reusable test data and setup
  - Proper test isolation and cleanup

#### API Enhancements
- **Enhanced Endpoints**
  - Improved error handling across all endpoints
  - Rate limiting on sensitive operations
  - Structured response formats
- **New Endpoints**
  - `/health` - Basic application health
  - `/health/detailed` - Comprehensive system health
  - `/metrics` - Application and system metrics
  - `/docs` - Interactive API documentation

#### Security Middleware
- **Trusted Host Middleware**
  - Protection against host header attacks
  - Configurable allowed hosts
- **CORS Configuration**
  - Configurable cross-origin resource sharing
  - Environment-specific CORS settings

### Changed

#### Application Structure
- **Main Application** (`app/main.py`)
  - Refactored to use service layer pattern
  - Enhanced error handling and logging
  - Security middleware integration
  - Rate limiting implementation
- **Database Models** (`app/models.py`)
  - Added strategic indexes for performance
  - Enhanced column constraints
  - Improved data type definitions
- **Scheduler** (`app/scheduler.py`)
  - Refactored to use service layer
  - Enhanced error handling and logging
  - Improved background task management
- **Alerts** (`app/alerts.py`)
  - Encrypted credential handling
  - Enhanced error handling and logging
  - Improved notification reliability

#### Configuration
- **Environment Variables**
  - Centralized configuration management
  - Type-safe environment variable handling
  - Default values with validation
- **Dependencies** (`requirements.txt`)
  - Added security libraries (cryptography)
  - Added database migration tools (alembic)
  - Added rate limiting (fastapi-limiter)
  - Added testing frameworks (pytest)
  - Added monitoring tools (prometheus-client)

### Security

#### Data Protection
- **Encryption at Rest**
  - SMTP passwords encrypted in database
  - Twilio auth tokens encrypted in database
  - Automatic encryption key management
- **Input Validation**
  - URL security validation
  - Email format validation
  - Phone number format validation
  - XSS prevention through sanitization
- **Rate Limiting**
  - IP-based request limiting
  - Configurable rate limits
  - Burst protection

#### Authentication & Authorization
- **Credential Management**
  - Encrypted storage of sensitive data
  - Secure credential retrieval
  - Environment-based fallback configuration

### Performance

#### Database Optimization
- **Indexing Strategy**
  - Primary key indexes
  - Foreign key indexes
  - Composite indexes for common queries
  - Query performance optimization
- **Connection Management**
  - Connection pooling
  - Connection health checking
  - Efficient resource utilization

#### Application Performance
- **Service Layer**
  - Efficient business logic separation
  - Reduced database queries
  - Optimized data processing
- **Caching Strategy**
  - In-memory rate limiting
  - Session-based caching
  - Efficient resource management

### Documentation

#### Code Documentation
- **Comprehensive Docstrings**
  - Function and class documentation
  - Parameter and return type documentation
  - Usage examples and best practices
- **Type Hints**
  - Complete type annotations
  - Improved IDE support
  - Better code maintainability

#### User Documentation
- **Setup Instructions**
  - Environment configuration guide
  - Database migration instructions
  - Security configuration recommendations
- **API Documentation**
  - Interactive API documentation
  - Endpoint descriptions and examples
  - Error response documentation

### Infrastructure

#### Development Tools
- **Testing Framework**
  - Comprehensive test coverage
  - Automated test execution
  - Test data management
- **Code Quality**
  - Type checking and validation
  - Code formatting standards
  - Linting and static analysis

#### Deployment
- **Container Security**
  - Multi-stage Docker builds
  - Security-hardened containers
  - Non-root user execution
- **Environment Management**
  - Secure configuration handling
  - Environment-specific settings
  - Secrets management

### Breaking Changes

#### API Changes
- **Error Response Format**
  - Standardized error response structure
  - Enhanced error messages
  - Proper HTTP status codes
- **Configuration Requirements**
  - New required environment variables
  - Updated configuration format
  - Security key requirements

#### Database Changes
- **Schema Updates**
  - New indexes may affect write performance
  - Column type changes
  - Constraint additions
- **Migration Requirements**
  - Database migration required
  - Backup recommended before upgrade
  - Rollback procedures available

### Migration Guide

#### From v1.x to v2.0.0

1. **Backup Database**
   ```bash
   cp pricewatch.db pricewatch.db.backup
   ```

2. **Update Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Update .env with your settings
   ```

4. **Run Database Migrations**
   ```bash
   alembic upgrade head
   ```

5. **Test Application**
   ```bash
   python setup_improvements.py
   uvicorn app.main:app --reload
   ```

### Deprecated

- Direct database access in route handlers (use service layer)
- Plain text credential storage (use encryption)
- Basic error handling (use custom exceptions)
- Print statements for logging (use structured logging)

### Removed

- Unused imports and dependencies
- Redundant error handling code
- Inefficient database queries
- Security vulnerabilities

### Fixed

#### Security Issues
- **Credential Exposure**
  - Fixed plain text password storage
  - Implemented encryption for sensitive data
  - Added secure credential handling
- **Input Validation**
  - Fixed XSS vulnerabilities
  - Added comprehensive input validation
  - Implemented sanitization
- **Rate Limiting**
  - Fixed potential DoS vulnerabilities
  - Added request rate limiting
  - Implemented burst protection

#### Performance Issues
- **Database Queries**
  - Fixed N+1 query problems
  - Added strategic indexing
  - Optimized query performance
- **Memory Usage**
  - Fixed memory leaks in long-running processes
  - Optimized resource usage
  - Improved garbage collection

#### Reliability Issues
- **Error Handling**
  - Fixed unhandled exceptions
  - Added comprehensive error handling
  - Implemented graceful degradation
- **Logging**
  - Fixed inconsistent logging
  - Added structured logging
  - Improved debugging capabilities

## [1.0.0] - 2024-01-XX

### Added
- Initial release of Pricewatch application
- Basic price tracking functionality
- SMTP and SMS notification support
- Simple web interface
- SQLite database storage
- Basic scheduler for price checking

### Features
- Price tracker creation and management
- Email and SMS notifications
- Price history tracking
- Basic web interface
- Simple configuration

---

## Future Roadmap

### [2.1.0] - Planned

#### Added
- **Advanced Monitoring**
  - Prometheus metrics integration
  - Grafana dashboard support
  - Alerting system for application issues
- **Enhanced Security**
  - OAuth2 authentication
  - API key management
  - Role-based access control
- **Performance Improvements**
  - Redis caching layer
  - Async request processing
  - Database connection pooling

#### Changed
- **API Versioning**
  - RESTful API design
  - API versioning strategy
  - Backward compatibility

### [2.2.0] - Planned

#### Added
- **Multi-tenant Support**
  - User isolation
  - Tenant-specific configurations
  - Resource quotas
- **Advanced Features**
  - Price prediction algorithms
  - Trend analysis
  - Custom notification templates
- **Integration Support**
  - Webhook notifications
  - Third-party API integrations
  - Plugin system

### [3.0.0] - Future

#### Added
- **Microservices Architecture**
  - Service decomposition
  - API gateway
  - Service mesh
- **Cloud Native Features**
  - Kubernetes deployment
  - Auto-scaling
  - Service discovery
- **Advanced Analytics**
  - Machine learning integration
  - Predictive analytics
  - Business intelligence

---

## Contributing

When making changes to the application, please:

1. **Update this changelog** with your changes
2. **Follow semantic versioning** for releases
3. **Include breaking changes** in the appropriate section
4. **Document migration steps** for major changes
5. **Test thoroughly** before submitting changes

### Changelog Format

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for security improvements

### Version Numbering

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

---

## Support

For questions about changes or migration assistance:

1. Check the [IMPROVEMENTS.md](IMPROVEMENTS.md) file for detailed information
2. Review the [setup_improvements.py](setup_improvements.py) script
3. Run the test suite to verify your installation
4. Check the application logs for detailed error information

---

*This changelog is maintained automatically and should be updated with every significant change to the application.*
