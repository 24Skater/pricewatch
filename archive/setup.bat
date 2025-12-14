@echo off
echo 🚀 Pricewatch v2.0 Setup for Windows
echo ====================================

echo.
echo 🔍 Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo.
echo 🐍 Creating virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo 📦 Installing dependencies...
.venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo 📝 Creating .env file...
if not exist .env (
    echo # Pricewatch Configuration > .env
    echo SECRET_KEY=your-super-secure-secret-key-change-this-in-production-minimum-32-characters >> .env
    echo DATABASE_URL=sqlite:///pricewatch.db >> .env
    echo ENVIRONMENT=development >> .env
    echo DEBUG=true >> .env
    echo LOG_LEVEL=INFO >> .env
    echo LOG_FORMAT=json >> .env
    echo RATE_LIMIT_PER_MINUTE=60 >> .env
    echo RATE_LIMIT_BURST=10 >> .env
    echo REQUEST_TIMEOUT=30 >> .env
    echo MAX_RETRIES=3 >> .env
    echo USE_JS_FALLBACK=false >> .env
    echo SCHEDULE_MINUTES=30 >> .env
    echo ✅ .env file created
) else (
    echo ✅ .env file already exists
)

echo.
echo 🗄️  Setting up database...
.venv\Scripts\alembic upgrade head
if %errorlevel% neq 0 (
    echo ❌ Failed to setup database
    pause
    exit /b 1
)

echo.
echo ✅ Setup completed successfully!
echo.
echo 📋 Next steps:
echo 1. Activate virtual environment: .venv\Scripts\activate
echo 2. Start application: .venv\Scripts\uvicorn app.main:app --reload
echo 3. Test application: python test_setup.py
echo.
echo 🔗 Useful URLs:
echo - http://localhost:8000 - Main application
echo - http://localhost:8000/health - Health check
echo - http://localhost:8000/docs - API documentation
echo.
pause
