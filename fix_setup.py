#!/usr/bin/env python3
"""
Fix script for Pricewatch v2.0 setup issues.
This script fixes common setup problems.
"""

import os
import sys
import subprocess
from pathlib import Path


def fix_pydantic_imports():
    """Fix Pydantic import issues."""
    print("🔧 Fixing Pydantic imports...")
    
    # Update requirements to ensure correct versions
    requirements_content = """fastapi>=0.111,<1
uvicorn[standard]>=0.30,<1
SQLAlchemy>=2.0,<3
pydantic>=2.8,<3
pydantic-settings>=2.3,<3
requests>=2.32,<3
beautifulsoup4>=4.12,<5
lxml>=5.2,<6
APScheduler>=3.10,<4
Jinja2>=3.1,<4
python-dotenv>=1.0,<2
twilio>=9.3,<10
email-validator>=2.2,<3
python-multipart>=0.0.20,<0.1
# Security and encryption
cryptography>=41.0,<42
# Database migrations
alembic>=1.12,<2
# Rate limiting
fastapi-limiter>=0.1.5,<1
# Testing
pytest>=7.4,<8
pytest-asyncio>=0.21,<1
# Monitoring (optional)
prometheus-client>=0.19,<1
"""
    
    Path("requirements.txt").write_text(requirements_content)
    print("✅ Requirements updated")
    
    # Reinstall dependencies
    if os.name == 'nt':  # Windows
        pip_cmd = ".venv\\Scripts\\pip"
    else:  # macOS/Linux
        pip_cmd = ".venv/bin/pip"
    
    print("🔄 Reinstalling dependencies...")
    result = subprocess.run([pip_cmd, "install", "-r", "requirements.txt", "--upgrade"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to reinstall dependencies: {result.stderr}")
        return False
    
    print("✅ Dependencies reinstalled")
    return True


def fix_database_setup():
    """Fix database setup issues."""
    print("🔧 Fixing database setup...")
    
    # Check if migrations directory exists
    if Path("migrations").exists():
        print("🔄 Removing existing migrations...")
        import shutil
        shutil.rmtree("migrations")
    
    # Check if database file exists
    if Path("pricewatch.db").exists():
        print("🔄 Removing existing database...")
        Path("pricewatch.db").unlink()
    
    # Determine the correct alembic command path
    if os.name == 'nt':  # Windows
        alembic_cmd = ".venv\\Scripts\\alembic"
    else:  # macOS/Linux
        alembic_cmd = ".venv/bin/alembic"
    
    # Initialize migrations
    print("🔄 Initializing migrations...")
    result = subprocess.run([alembic_cmd, "init", "migrations"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to initialize migrations: {result.stderr}")
        return False
    
    # Create initial migration
    print("🔄 Creating initial migration...")
    result = subprocess.run([alembic_cmd, "revision", "--autogenerate", "-m", "Initial migration"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to create migration: {result.stderr}")
        return False
    
    # Apply migrations
    print("🔄 Applying migrations...")
    result = subprocess.run([alembic_cmd, "upgrade", "head"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to apply migrations: {result.stderr}")
        return False
    
    print("✅ Database setup completed")
    return True


def test_application():
    """Test if the application can start."""
    print("🧪 Testing application...")
    
    if os.name == 'nt':  # Windows
        uvicorn_cmd = ".venv\\Scripts\\uvicorn"
    else:  # macOS/Linux
        uvicorn_cmd = ".venv/bin/uvicorn"
    
    # Test if uvicorn is available
    result = subprocess.run([uvicorn_cmd, "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Uvicorn not found: {uvicorn_cmd}")
        return False
    
    print("✅ Uvicorn found")
    return True


def main():
    """Main fix function."""
    print("🔧 Pricewatch v2.0 Setup Fix")
    print("=" * 50)
    
    # Fix Pydantic imports
    if not fix_pydantic_imports():
        print("\n❌ Fix failed: Pydantic import issues")
        sys.exit(1)
    
    # Fix database setup
    if not fix_database_setup():
        print("\n❌ Fix failed: Database setup issues")
        sys.exit(1)
    
    # Test application
    if not test_application():
        print("\n❌ Fix failed: Application test failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Fix completed successfully!")
    print("\n📋 Next steps:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':  # Windows
        print("   .venv\\Scripts\\activate")
    else:  # macOS/Linux
        print("   source .venv/bin/activate")
    
    print("2. Start the application:")
    if os.name == 'nt':  # Windows
        print("   .venv\\Scripts\\uvicorn app.main:app --reload")
    else:  # macOS/Linux
        print("   .venv/bin/uvicorn app.main:app --reload")
    
    print("3. Test the application:")
    print("   python test_setup.py")
    
    print("\n🔗 Useful URLs:")
    print("- http://localhost:8000 - Main application")
    print("- http://localhost:8000/health - Health check")
    print("- http://localhost:8000/docs - API documentation")


if __name__ == "__main__":
    main()
