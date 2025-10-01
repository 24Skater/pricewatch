# PowerShell script to fix migrations
Write-Host "🔧 Fixing Pricewatch migrations..." -ForegroundColor Green

# Remove migrations directory if it exists
if (Test-Path "migrations") {
    Write-Host "🗑️  Removing existing migrations directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "migrations"
    Write-Host "✅ Migrations directory removed" -ForegroundColor Green
}

# Remove database file if it exists
if (Test-Path "pricewatch.db") {
    Write-Host "🗑️  Removing existing database..." -ForegroundColor Yellow
    Remove-Item "pricewatch.db"
    Write-Host "✅ Database file removed" -ForegroundColor Green
}

# Initialize migrations
Write-Host "🔄 Initializing Alembic migrations..." -ForegroundColor Yellow
.venv\Scripts\alembic init migrations
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to initialize migrations" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Migrations initialized" -ForegroundColor Green

# Create initial migration
Write-Host "🔄 Creating initial migration..." -ForegroundColor Yellow
.venv\Scripts\alembic revision --autogenerate -m "Initial migration"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create migration" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Initial migration created" -ForegroundColor Green

# Apply migrations
Write-Host "🔄 Applying migrations..." -ForegroundColor Yellow
.venv\Scripts\alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to apply migrations" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Migrations applied" -ForegroundColor Green

Write-Host "🎉 Database setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Start the application: .venv\Scripts\uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "2. Test the application: python test_setup.py" -ForegroundColor White
Write-Host "3. Visit: http://localhost:8000" -ForegroundColor White
