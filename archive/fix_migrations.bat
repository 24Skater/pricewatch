@echo off
echo 🔧 Fixing Pricewatch migrations...

echo.
echo 🗑️  Removing existing migrations directory...
if exist migrations rmdir /s /q migrations

echo.
echo 🗑️  Removing existing database...
if exist pricewatch.db del pricewatch.db

echo.
echo 🔄 Initializing Alembic migrations...
.venv\Scripts\alembic init migrations
if %errorlevel% neq 0 (
    echo ❌ Failed to initialize migrations
    pause
    exit /b 1
)

echo.
echo 🔄 Creating initial migration...
.venv\Scripts\alembic revision --autogenerate -m "Initial migration"
if %errorlevel% neq 0 (
    echo ❌ Failed to create migration
    pause
    exit /b 1
)

echo.
echo 🔄 Applying migrations...
.venv\Scripts\alembic upgrade head
if %errorlevel% neq 0 (
    echo ❌ Failed to apply migrations
    pause
    exit /b 1
)

echo.
echo ✅ Database setup completed successfully!
echo.
echo 📋 Next steps:
echo 1. Start the application: .venv\Scripts\uvicorn app.main:app --reload
echo 2. Test the application: python test_setup.py
echo 3. Visit: http://localhost:8000
echo.
pause
