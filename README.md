# Pricewatch v2.1 - Enterprise Price Tracking Application

[![CI](https://github.com/pricewatch/pricewatch/workflows/CI/badge.svg)](https://github.com/pricewatch/pricewatch/actions)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](https://github.com/pricewatch/pricewatch)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Pricewatch** is a comprehensive price tracking application that monitors product prices across the web and sends notifications when prices change. Built with FastAPI and featuring enterprise-grade security, monitoring, and scalability features.

## 📑 Table of Contents

- [What is Pricewatch?](#-what-is-pricewatch)
- [Quick Start](#-quick-start)
- [How to Use](#-how-to-use)
- [Configuration](#-configuration)
- [Architecture](#-architecture)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Security](#-security)
- [Built With](#-built-with)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)
- [Acknowledgments](#-acknowledgments)

## 🎯 What is Pricewatch?

Pricewatch is a web application that helps you:

- **Track Product Prices**: Monitor prices from any e-commerce website
- **Get Price Alerts**: Receive email or SMS notifications when prices drop
- **Manage Multiple Trackers**: Track hundreds of products simultaneously
- **View Price History**: See price trends and changes over time
- **Custom Notifications**: Set up personalized notification profiles

### Key Features

- 🔒 **Enterprise Security**: Encryption, input validation, rate limiting
- 🏗️ **Modern Architecture**: Service layer, proper separation of concerns
- 📊 **Monitoring & Logging**: Health checks, metrics, structured logging
- 🗄️ **Database Optimization**: Strategic indexing, migrations
- 🧪 **Comprehensive Testing**: Unit, integration, and security tests
- 🚀 **Production Ready**: Docker support, environment configuration

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** - Download from [python.org](https://python.org)
- **Git** - Download from [git-scm.com](https://git-scm.com)

### Installation

1. **Clone the Repository**
   ```bash
   git clone <your-repo-url>
   cd pricewatch
   ```

2. **Create Virtual Environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   # Copy example configuration
   cp .env.example .env
   
   # Edit .env file with your settings
   # Set SECRET_KEY=your-super-secure-secret-key-minimum-32-characters
   ```

5. **Setup Database**
   ```bash
   # Initialize migrations
   alembic upgrade head
   ```

6. **Start Application**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

7. **Test Installation**
   ```bash
   python test_setup.py
   ```

### 🎉 You're Ready!

Visit http://localhost:8000 to start using Pricewatch!

## 📖 How to Use

### 1. **Create Your First Tracker**

1. Go to http://localhost:8000
2. Click "Add Tracker"
3. Enter a product URL (e.g., from Amazon, eBay, etc.)
4. Choose notification method (Email or SMS)
5. Enter your contact information
6. Click "Create Tracker"

### 2. **Set Up Notifications**

#### Email Notifications
1. Go to **Admin** → **Profiles**
2. Click "Create New Profile"
3. Enter your SMTP settings:
   - SMTP Host (e.g., smtp.gmail.com)
   - SMTP Port (usually 587)
   - Username and Password
   - From Email address

#### SMS Notifications
1. Sign up for [Twilio](https://twilio.com)
2. Get your Account SID, Auth Token, and Phone Number
3. Create a notification profile with Twilio settings

### 3. **Manage Trackers**

- **View All Trackers**: Main page shows all your trackers
- **Edit Tracker**: Click on any tracker to edit settings
- **Delete Tracker**: Remove trackers you no longer need
- **Refresh Price**: Manually check for price updates
- **View History**: See price changes over time

### 4. **Monitor Your Application**

- **Health Check**: http://localhost:8000/health
- **Detailed Health**: http://localhost:8000/health/detailed
- **API Documentation**: http://localhost:8000/docs
- **Application Logs**: Check `app.log` file

## 🔧 Configuration

### Environment Variables

Create a `.env` file with these settings:

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

# Scraping
REQUEST_TIMEOUT=30
MAX_RETRIES=3
USE_JS_FALLBACK=false
SCHEDULE_MINUTES=30

# SMTP (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
FROM_EMAIL=your-email@gmail.com

# Twilio (Optional)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_FROM_NUMBER=your-twilio-number
```

### Advanced Configuration

- **Database**: Change `DATABASE_URL` for PostgreSQL/MySQL
- **Logging**: Set `LOG_FORMAT=json` for structured logs
- **Monitoring**: Enable `ENABLE_METRICS=true` for Prometheus
- **Security**: Configure `ALLOWED_HOSTS` for production

## 🏗️ Architecture

### System Overview

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

### Service Layer
- **TrackerService**: Business logic for price trackers
- **ProfileService**: Notification profile management
- **SchedulerService**: Background price checking
- **NotificationService**: Centralized notification handling

### Security Features
- **Encryption**: Sensitive data encrypted at rest using Fernet
- **Validation**: Comprehensive input validation with Pydantic
- **Rate Limiting**: Protection against abuse with automatic cleanup
- **XSS Prevention**: Input sanitization and output encoding
- **CSRF Protection**: Token-based CSRF protection on all forms
- **Security Headers**: Comprehensive security headers middleware
- **SSRF Protection**: URL validation preventing private IP access
- **Request Tracking**: Full request lifecycle tracking with UUIDs

### Database
- **SQLAlchemy ORM**: Object-relational mapping
- **Alembic Migrations**: Database versioning
- **Strategic Indexing**: Query performance optimization
- **Connection Pooling**: Efficient resource usage (PostgreSQL)

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_security.py -v
python -m pytest tests/test_api.py -v
python -m pytest tests/test_services.py -v
python -m pytest tests/test_scraper.py -v
python -m pytest tests/test_notifications.py -v
python -m pytest tests/test_integration.py -v
python -m pytest tests/test_monitoring.py -v
```

### Test Coverage
```bash
# Run with coverage report
python -m pytest tests/ --cov=app --cov-report=html

# Run with coverage and fail if below 80%
python -m pytest tests/ --cov=app --cov-fail-under=80

# Generate coverage report
python -m pytest tests/ --cov=app --cov-report=term-missing
```

### Coverage Requirements
- **Minimum coverage**: 80%
- **Coverage configuration**: See `.coveragerc`
- **HTML report**: Generated in `htmlcov/` directory
- **CI enforcement**: Coverage check runs on every PR

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t pricewatch .

# Run container
docker run -p 8000:8000 --env-file .env pricewatch
```

### Production Considerations
- Set secure `SECRET_KEY`
- Use production database (PostgreSQL/MySQL)
- Configure proper logging
- Set up monitoring and alerting
- Use reverse proxy (nginx)
- Enable HTTPS

## 📊 Monitoring

### Health Checks
- **Basic**: http://localhost:8000/health
- **Detailed**: http://localhost:8000/health/detailed
- **Metrics**: http://localhost:8000/metrics

### Logging
- **Structured Logs**: JSON format in `app.log`
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Contextual Information**: Request IDs, user context

## 🔒 Security

### Data Protection
- **Encryption at Rest**: Sensitive data encrypted
- **Input Validation**: Comprehensive validation
- **Rate Limiting**: Protection against abuse
- **XSS Prevention**: Input sanitization

### Best Practices
- Use strong, unique SECRET_KEY
- Configure proper CORS settings
- Set up firewall rules
- Regular security updates
- Monitor access logs

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass (`pytest tests/`)
6. Run pre-commit hooks (`pre-commit run --all-files`)
7. Commit your changes (`git commit -m 'feat: add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## 🛠️ Built With

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast web framework for building APIs
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - SQL toolkit and ORM
- **[Alembic](https://alembic.sqlalchemy.org/)** - Database migration tool
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** - HTML parsing and scraping
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation using Python type annotations
- **[Jinja2](https://jinja.palletsprojects.com/)** - Template engine
- **[Cryptography](https://cryptography.io/)** - Encryption and security
- **[Ruff](https://github.com/astral-sh/ruff)** - Fast Python linter and formatter
- **[Pytest](https://pytest.org/)** - Testing framework
- **[Docker](https://www.docker.com/)** - Containerization

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Troubleshooting
- Check application logs in `app.log`
- Verify environment configuration
- Run health checks
- Check database connectivity

### Common Issues
- **Import Errors**: Ensure virtual environment is activated
- **Database Errors**: Run `alembic upgrade head`
- **Port Conflicts**: Use different port with `--port 8001`
- **Permission Errors**: Check file permissions

### Getting Help
- Check the [IMPROVEMENTS.md](IMPROVEMENTS.md) file
- Review the [CHANGELOG.md](CHANGELOG.md)
- Run `python test_setup.py` for diagnostics

## 🙏 Acknowledgments

- **Contributor Covenant** - For the Code of Conduct template
- **FastAPI Community** - For excellent documentation and support
- **All Contributors** - Thank you to everyone who has contributed to Pricewatch!

---

**Pricewatch v2.1** - Enterprise-grade price tracking made simple! 🚀
