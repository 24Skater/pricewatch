@echo off
echo 🔄 Creating initial migration...

.venv\Scripts\alembic revision --autogenerate -m "Initial migration"
if %errorlevel% neq 0 (
    echo ❌ Failed to create migration
    pause
    exit /b 1
)

echo ✅ Migration created successfully!

echo.
echo 🔄 Applying migrations...

.venv\Scripts\alembic upgrade head
if %errorlevel% neq 0 (
    echo ❌ Failed to apply migrations
    pause
    exit /b 1
)

echo ✅ Migrations applied successfully!
echo.
echo 🎉 Database setup completed!
echo.
echo 📋 Next steps:
echo 1. Start the application: .venv\Scripts\uvicorn app.main:app --reload
echo 2. Test the application: python test_setup.py
echo 3. Visit: http://localhost:8000
echo.
pause
