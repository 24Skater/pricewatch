# Pricewatch v2.0 - Setup Guide for New PC

This guide will help you set up and test the improved Pricewatch application on a fresh PC.

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** - Download from [python.org](https://python.org)
2. **Git** - Download from [git-scm.com](https://git-scm.com)
3. **Code Editor** - VS Code, PyCharm, or any preferred editor

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone <your-repo-url>
cd pricewatch

# Or if you have the files locally, navigate to the directory
cd /path/to/pricewatch
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install pytest pytest-asyncio
```

### Step 4: Configure Environment

```bash
# Create environment file
cp .env.example .env

# Edit the .env file with your settings
# Windows: notepad .env
# macOS/Linux: nano .env
```

**Important Environment Variables:**
```env
# Required - Set a secure secret key (minimum 32 characters)
SECRET_KEY=your-super-secure-secret-key-change-this-in-production

# Database (default is fine for testing)
DATABASE_URL=sqlite:///pricewatch.db

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### Step 5: Initialize Database

```bash
# Initialize Alembic migrations
alembic init migrations

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### Step 6: Run the Application

```bash
# Start the application
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 7: Test the Application

Open your browser and visit:
- **Main App**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **Detailed Health**: http://localhost:8000/health/detailed

## 🧪 Testing the Improvements

### 1. Basic Functionality Test

1. **Create a Tracker**
   - Go to http://localhost:8000
   - Click "Add Tracker"
   - Enter a product URL (e.g., https://example.com/product)
   - Select notification method (email/sms)
   - Enter contact information
   - Click "Create Tracker"

2. **Test Price Refresh**
   - Go to your tracker page
   - Click "Refresh Price" or "Poll Now"
   - Check if price is detected and stored

### 2. Security Features Test

1. **Input Validation**
   - Try creating a tracker with invalid URL
   - Try invalid email format
   - Check that validation errors are shown

2. **Rate Limiting**
   - Make multiple rapid requests
   - Check that rate limiting kicks in

### 3. Monitoring Features Test

1. **Health Checks**
   ```bash
   # Test basic health
   curl http://localhost:8000/health
   
   # Test detailed health
   curl http://localhost:8000/health/detailed
   ```

2. **Metrics**
   ```bash
   # Test metrics endpoint
   curl http://localhost:8000/metrics
   ```

### 4. Database Features Test

1. **Check Database**
   ```bash
   # View database file
   ls -la pricewatch.db
   
   # Check database content (optional)
   sqlite3 pricewatch.db ".tables"
   sqlite3 pricewatch.db "SELECT * FROM trackers;"
   ```

### 5. Logging Test

1. **Check Logs**
   ```bash
   # View application logs
   tail -f app.log
   
   # Check for structured JSON logs
   cat app.log | jq .
   ```

## 🔧 Configuration Options

### Email Notifications (Optional)

If you want to test email notifications:

```env
# Add to .env file
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
FROM_EMAIL=your-email@gmail.com
```

### SMS Notifications (Optional)

If you want to test SMS notifications:

```env
# Add to .env file
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_FROM_NUMBER=your-twilio-number
```

## 🧪 Running Tests

### Run All Tests
```bash
# Run complete test suite
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

### Run Specific Tests
```bash
# Test security features
python -m pytest tests/test_security.py -v

# Test API endpoints
python -m pytest tests/test_api.py -v

# Test services
python -m pytest tests/test_services.py -v
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure you're in the virtual environment
   which python
   # Should show path to .venv/bin/python
   ```

2. **Database Errors**
   ```bash
   # Reset database
   rm pricewatch.db
   alembic upgrade head
   ```

3. **Port Already in Use**
   ```bash
   # Use different port
   uvicorn app.main:app --reload --port 8001
   ```

4. **Permission Errors**
   ```bash
   # On Windows, run as administrator
   # On macOS/Linux, check file permissions
   chmod +x setup_improvements.py
   ```

### Check Application Status

1. **Health Check**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "healthy", "version": "2.0.0", "environment": "development"}
   ```

2. **Detailed Health**
   ```bash
   curl http://localhost:8000/health/detailed
   # Should return comprehensive health information
   ```

3. **Check Logs**
   ```bash
   # Look for errors in logs
   grep -i error app.log
   grep -i warning app.log
   ```

## 📊 Monitoring the Application

### Real-time Monitoring

1. **Application Logs**
   ```bash
   # Follow logs in real-time
   tail -f app.log
   ```

2. **System Resources**
   ```bash
   # Check system resources
   curl http://localhost:8000/metrics
   ```

3. **Database Status**
   ```bash
   # Check database health
   curl http://localhost:8000/health/detailed | jq '.checks.database'
   ```

### Performance Testing

1. **Load Testing** (Optional)
   ```bash
   # Install Apache Bench
   # On Windows: Download from Apache website
   # On macOS: brew install httpd
   # On Linux: apt-get install apache2-utils
   
   # Run load test
   ab -n 100 -c 10 http://localhost:8000/health
   ```

## 🎯 Success Criteria

Your setup is successful if:

1. ✅ Application starts without errors
2. ✅ Health check returns "healthy" status
3. ✅ You can create and manage trackers
4. ✅ Price refresh functionality works
5. ✅ Logs are generated in structured format
6. ✅ All tests pass
7. ✅ Security features work (validation, rate limiting)
8. ✅ Monitoring endpoints return data

## 🚀 Next Steps

Once everything is working:

1. **Configure Production Settings**
   - Set secure SECRET_KEY
   - Configure production database
   - Set up proper logging

2. **Set Up Monitoring**
   - Configure external monitoring
   - Set up alerting
   - Monitor performance

3. **Deploy to Production**
   - Use Docker for deployment
   - Set up reverse proxy
   - Configure SSL certificates

## 📞 Getting Help

If you encounter issues:

1. **Check the logs** - Look for error messages
2. **Verify configuration** - Ensure .env file is correct
3. **Run tests** - Check if tests pass
4. **Check health endpoints** - Verify application status
5. **Review documentation** - Check IMPROVEMENTS.md and CHANGELOG.md

## 🎉 Congratulations!

If you've reached this point, you have successfully:
- Set up the improved Pricewatch application
- Tested all the new features
- Verified security improvements
- Confirmed monitoring capabilities

The application is now ready for development and testing with enterprise-grade features!
