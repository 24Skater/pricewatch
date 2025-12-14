# Pricewatch

> **Enterprise-grade price tracking made simple** — Monitor product prices across the web and get instant notifications when prices drop.

[![CI](https://img.shields.io/github/actions/workflow/status/pricewatch/pricewatch/ci.yml?branch=main&label=CI&logo=github)](https://github.com/pricewatch/pricewatch/actions)
[![Coverage](https://img.shields.io/badge/coverage-80.67%25-brightgreen?logo=codecov)](https://github.com/pricewatch/pricewatch)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?logo=opensourceinitiative)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

---

## ✨ Features

- 🔍 **Smart Price Tracking** — Monitor prices from any e-commerce website with flexible CSS selectors
- 📧 **Multi-Channel Notifications** — Get alerts via email (SMTP) or SMS (Twilio) when prices change
- 📊 **Price History** — Track price trends and changes over time with detailed history
- 🔒 **Enterprise Security** — Encryption, CSRF protection, rate limiting, and comprehensive input validation
- 🚀 **Production Ready** — Docker support, health checks, Prometheus metrics, and structured logging
- 🧪 **Well Tested** — 80.67% test coverage with comprehensive unit, integration, and security tests
- ⚡ **High Performance** — Async HTTP client, database connection pooling, and optimized queries
- 📱 **Modern Web UI** — Clean, responsive interface for managing trackers and profiles

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **Docker** (optional, for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/pricewatch/pricewatch.git
   cd pricewatch
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy example configuration
   cp .env.example .env

   # Edit .env and set at minimum:
   # SECRET_KEY=your-super-secure-secret-key-minimum-32-characters
   # DATABASE_URL=sqlite:///pricewatch.db
   ```

5. **Initialize database**
   ```bash
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

7. **Open your browser**
   ```
   http://localhost:8000
   ```

🎉 **You're all set!** Start tracking prices by adding your first tracker.

## 📖 Usage

### Creating a Price Tracker

1. Navigate to the home page at `http://localhost:8000`
2. Click **"Add Tracker"**
3. Enter the product URL (e.g., from Amazon, eBay, or any e-commerce site)
4. Optionally specify a CSS selector for the price element
5. Choose your notification method (Email or SMS)
6. Enter your contact information
7. Click **"Create Tracker"**

### Setting Up Notifications

#### Email Notifications

1. Go to **Admin → Profiles**
2. Click **"Create New Profile"**
3. Configure SMTP settings:
   - SMTP Host (e.g., `smtp.gmail.com`)
   - SMTP Port (usually `587` for TLS)
   - Username and Password
   - From Email address

#### SMS Notifications

1. Sign up for [Twilio](https://www.twilio.com/)
2. Get your Account SID, Auth Token, and Phone Number
3. Create a notification profile with your Twilio credentials

### Managing Trackers

- **View All Trackers** — Main dashboard shows all active trackers
- **Edit Tracker** — Click any tracker to modify settings
- **Delete Tracker** — Remove trackers you no longer need
- **Manual Refresh** — Check for price updates on demand
- **Price History** — View detailed price change history

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required
SECRET_KEY=your-super-secure-secret-key-minimum-32-characters
DATABASE_URL=sqlite:///pricewatch.db

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Security
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10
ALLOWED_HOSTS=localhost,127.0.0.1

# Scraping
REQUEST_TIMEOUT=30
MAX_RETRIES=3
SCHEDULE_MINUTES=30
USE_ASYNC_CLIENT=false

# SMTP (Optional - for email notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
FROM_EMAIL=your-email@gmail.com

# Twilio (Optional - for SMS notifications)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_FROM_NUMBER=your-twilio-number

# Database (Optional - for PostgreSQL/MySQL)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
```

### Production Configuration

For production deployments:

- Use **PostgreSQL** or **MySQL** instead of SQLite
- Set `ENVIRONMENT=production` and `DEBUG=false`
- Configure proper `ALLOWED_HOSTS`
- Use a strong, randomly generated `SECRET_KEY`
- Enable HTTPS with a reverse proxy (nginx)
- Set up proper logging and monitoring

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Pricewatch v2.1                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Web UI     │    │   REST API   │    │  Health API  │ │
│  │  (Templates) │    │  (FastAPI)   │    │  (Monitoring)│ │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘ │
│         │                   │                    │         │
│         └───────────────────┼────────────────────┘         │
│                             │                              │
│                    ┌────────▼────────┐                     │
│                    │  Service Layer  │                     │
│                    ├─────────────────┤                     │
│                    │ TrackerService  │                     │
│                    │ ProfileService  │                     │
│                    │SchedulerService │                     │
│                    │NotificationSvc  │                     │
│                    └────────┬────────┘                     │
│                             │                              │
│         ┌───────────────────┼───────────────────┐          │
│         │                   │                   │          │
│  ┌──────▼──────┐   ┌────────▼────────┐  ┌──────▼──────┐  │
│  │   Scraper   │   │   Database      │  │  Security   │  │
│  │  (Price     │   │  (SQLAlchemy)   │  │  (Encrypt,  │  │
│  │ Extraction) │   │                 │  │  Validate,  │  │
│  └─────────────┘   └─────────────────┘  │  Rate Limit)│  │
│                                          └─────────────┘  │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              External Services                      │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │  │
│  │  │   SMTP   │  │  Twilio  │  │  Web     │         │  │
│  │  │  (Email) │  │   (SMS)  │  │ Scraping │         │  │
│  │  └──────────┘  └──────────┘  └──────────┘         │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Key Components

- **Service Layer** — Business logic separation with `TrackerService`, `ProfileService`, `SchedulerService`, and `NotificationService`
- **Security Layer** — Encryption, validation, rate limiting, CSRF protection, and security headers
- **Database Layer** — SQLAlchemy ORM with Alembic migrations and connection pooling
- **Scraping Engine** — Flexible price extraction with CSS selectors and async HTTP support

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test categories
pytest tests/test_security.py -v      # Security tests
pytest tests/test_api.py -v           # API endpoint tests
pytest tests/test_services.py -v      # Service layer tests
pytest tests/test_scraper.py -v       # Scraper tests
pytest tests/test_integration.py -v   # Integration tests
```

### Coverage

- **Current Coverage**: 80.67%
- **Minimum Required**: 75%
- **HTML Report**: Generated in `htmlcov/` directory

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=75
```

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Build the image
docker build -t pricewatch:latest .

# Run the container
docker run -p 8000:8000 --env-file .env pricewatch:latest
```

### Docker Compose

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

The Docker setup includes:
- Multi-stage builds for optimized image size
- Non-root user for security
- Health checks
- Resource limits
- Persistent volumes for database

## 📊 Monitoring & Health Checks

### Endpoints

- **Basic Health**: `http://localhost:8000/health`
- **Detailed Health**: `http://localhost:8000/health/detailed`
- **Prometheus Metrics**: `http://localhost:8000/metrics`
- **API Documentation**: `http://localhost:8000/docs`

### Logging

Pricewatch uses structured JSON logging with:
- Request ID tracking for full request lifecycle
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Sensitive data masking (passwords, tokens automatically redacted)
- Contextual information (user, request, error details)

## 🔒 Security Features

- **🔐 Encryption at Rest** — Sensitive data encrypted using Fernet (Fernet symmetric encryption)
- **🛡️ CSRF Protection** — Token-based protection on all forms
- **🚦 Rate Limiting** — IP-based rate limiting with automatic cleanup
- **✅ Input Validation** — Comprehensive validation with Pydantic schemas
- **🔍 SSRF Protection** — URL validation preventing private IP access
- **📋 Security Headers** — X-Content-Type-Options, X-Frame-Options, CSP, and more
- **🔑 Request Tracking** — Unique request IDs for full observability

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) |
| **Database** | [SQLAlchemy](https://www.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/) |
| **Validation** | [Pydantic](https://docs.pydantic.dev/) |
| **Scraping** | [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) + [httpx](https://www.python-httpx.org/) |
| **Templates** | [Jinja2](https://jinja.palletsprojects.com/) |
| **Security** | [Cryptography](https://cryptography.io/) |
| **Testing** | [Pytest](https://pytest.org/) |
| **Linting** | [Ruff](https://github.com/astral-sh/ruff) |
| **Type Checking** | [MyPy](https://mypy.readthedocs.io/) |
| **Monitoring** | [Prometheus](https://prometheus.io/) |

## 📁 Project Structure

```
pricewatch/
├── app/                    # Main application code
│   ├── services/          # Business logic layer
│   ├── static/            # CSS and static assets
│   └── templates/         # HTML templates
├── docs/                  # Documentation
│   ├── CHANGELOG.md
│   ├── CONTRIBUTING.md
│   ├── SECURITY.md
│   └── ...
├── tests/                 # Test suite
├── migrations/            # Database migrations
├── docker-compose.yml     # Docker Compose config
├── Dockerfile             # Docker image definition
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
└── README.md             # This file
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for details.

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Add tests** for new features
5. **Ensure all tests pass** (`pytest tests/`)
6. **Run pre-commit hooks** (`pre-commit run --all-files`)
7. **Commit your changes** (`git commit -m 'feat: add amazing feature'`)
8. **Push to the branch** (`git push origin feature/amazing-feature`)
9. **Open a Pull Request**

Please read our [Code of Conduct](docs/CODE_OF_CONDUCT.md) before contributing.

## 📝 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Troubleshooting

### Common Issues

- **Import Errors** → Ensure virtual environment is activated
- **Database Errors** → Run `alembic upgrade head`
- **Port Conflicts** → Use different port: `--port 8001`
- **Permission Errors** → Check file permissions

### Getting Help

- 📖 Check the [Documentation](docs/)
- 📋 Review the [Changelog](docs/CHANGELOG.md)
- 🔒 Read the [Security Policy](docs/SECURITY.md)
- 🐛 [Open an Issue](https://github.com/pricewatch/pricewatch/issues)

## 🗺️ Roadmap

- [ ] OAuth2 authentication
- [ ] API key management
- [ ] Redis caching layer
- [ ] Webhook notifications
- [ ] Multi-tenant support
- [ ] Price prediction algorithms
- [ ] Grafana dashboard integration

See [docs/IMPROVEMENT_PLAN.md](docs/IMPROVEMENT_PLAN.md) for detailed roadmap.

## 🙏 Acknowledgments

- **FastAPI Community** — For excellent documentation and support
- **Contributor Covenant** — For the Code of Conduct template
- **All Contributors** — Thank you to everyone who has contributed to Pricewatch!

---

<div align="center">

**Made with ❤️ by the Pricewatch Team**

[⭐ Star us on GitHub](https://github.com/pricewatch/pricewatch) • [📖 Documentation](docs/) • [🐛 Report Bug](https://github.com/pricewatch/pricewatch/issues) • [💡 Request Feature](https://github.com/pricewatch/pricewatch/issues)

</div>
