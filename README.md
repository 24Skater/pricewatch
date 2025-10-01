# Pricewatch v2.0 - Enterprise Price Tracking Application

**Pricewatch** is a comprehensive price tracking application that monitors product prices across the web and sends notifications when prices change. Built with FastAPI and featuring enterprise-grade security, monitoring, and scalability features.

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

- **Python 3.8+** - Download from [python.org](https://python.org)
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

### Service Layer
- **TrackerService**: Business logic for price trackers
- **ProfileService**: Notification profile management
- **SchedulerService**: Background price checking

### Security Features
- **Encryption**: Sensitive data encrypted at rest
- **Validation**: Comprehensive input validation
- **Rate Limiting**: Protection against abuse
- **XSS Prevention**: Input sanitization

### Database
- **SQLAlchemy ORM**: Object-relational mapping
- **Alembic Migrations**: Database versioning
- **Strategic Indexing**: Query performance optimization
- **Connection Pooling**: Efficient resource usage

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_security.py -v
python -m pytest tests/test_api.py -v
python -m pytest tests/test_services.py -v
```

### Test Coverage
```bash
# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

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

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

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

---

**Pricewatch v2.0** - Enterprise-grade price tracking made simple! 🚀
