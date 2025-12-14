#!/usr/bin/env python3
"""
Manual setup script for Pricewatch v2.0.
This script provides step-by-step instructions for setting up the application.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_requirements():
    """Check if all required files exist."""
    print("🔍 Checking requirements...")
    
    required_files = [
        "requirements.txt",
        "alembic.ini",
        "app/main.py",
        "app/config.py",
        "app/models.py",
        "app/database.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files found")
    return True


def setup_virtual_environment():
    """Setup virtual environment."""
    print("\n🐍 Setting up virtual environment...")
    
    if not Path(".venv").exists():
        print("Creating virtual environment...")
        result = subprocess.run([sys.executable, "-m", "venv", ".venv"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to create virtual environment: {result.stderr}")
            return False
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")
    
    return True


def install_dependencies():
    """Install dependencies."""
    print("\n📦 Installing dependencies...")
    
    if os.name == 'nt':  # Windows
        pip_cmd = ".venv\\Scripts\\pip"
    else:  # macOS/Linux
        pip_cmd = ".venv/bin/pip"
    
    result = subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to install dependencies: {result.stderr}")
        return False
    
    print("✅ Dependencies installed")
    return True


def create_env_file():
    """Create .env file."""
    print("\n📝 Creating .env file...")
    
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Pricewatch Configuration
SECRET_KEY=your-super-secure-secret-key-change-this-in-production-minimum-32-characters
DATABASE_URL=sqlite:///pricewatch.db
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
LOG_FORMAT=json
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10
REQUEST_TIMEOUT=30
MAX_RETRIES=3
USE_JS_FALLBACK=false
SCHEDULE_MINUTES=30
"""
        env_file.write_text(env_content)
        print("✅ .env file created")
    else:
        print("✅ .env file already exists")
    
    return True


def setup_database():
    """Setup database with migrations."""
    print("\n🗄️  Setting up database...")
    
    # Check if alembic.ini exists
    if not Path("alembic.ini").exists():
        print("❌ alembic.ini not found. Please ensure it exists.")
        return False
    
    # Determine the correct alembic command path
    if os.name == 'nt':  # Windows
        alembic_cmd = ".venv\\Scripts\\alembic"
    else:  # macOS/Linux
        alembic_cmd = ".venv/bin/alembic"
    
    # Check if alembic is available
    result = subprocess.run([alembic_cmd, "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Alembic not found. Please install it: {alembic_cmd}")
        return False
    
    print("✅ Alembic found")
    
    # Initialize migrations if they don't exist
    if not Path("migrations").exists():
        print("Initializing Alembic...")
        result = subprocess.run([alembic_cmd, "init", "migrations"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to initialize Alembic: {result.stderr}")
            return False
        print("✅ Alembic initialized")
    
    # Create initial migration
    print("Creating initial migration...")
    result = subprocess.run([alembic_cmd, "revision", "--autogenerate", "-m", "Initial migration"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to create migration: {result.stderr}")
        return False
    print("✅ Initial migration created")
    
    # Apply migrations
    print("Applying migrations...")
    result = subprocess.run([alembic_cmd, "upgrade", "head"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to apply migrations: {result.stderr}")
        return False
    print("✅ Migrations applied")
    
    return True


def test_application():
    """Test if the application can start."""
    print("\n🧪 Testing application...")
    
    if os.name == 'nt':  # Windows
        uvicorn_cmd = ".venv\\Scripts\\uvicorn"
    else:  # macOS/Linux
        uvicorn_cmd = ".venv/bin/uvicorn"
    
    # Test if uvicorn is available
    result = subprocess.run([uvicorn_cmd, "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Uvicorn not found. Please install it: {uvicorn_cmd}")
        return False
    
    print("✅ Uvicorn found")
    return True


def main():
    """Main setup function."""
    print("🚀 Pricewatch v2.0 Manual Setup")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Setup failed: Missing required files")
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        print("\n❌ Setup failed: Virtual environment creation failed")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed: Dependency installation failed")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("\n❌ Setup failed: .env file creation failed")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("\n❌ Setup failed: Database setup failed")
        sys.exit(1)
    
    # Test application
    if not test_application():
        print("\n❌ Setup failed: Application test failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
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
    
    print("\n⚠️  Important:")
    print("- Update SECRET_KEY in .env file for production")
    print("- Configure SMTP/Twilio credentials if needed")
    print("- Check app.log for application logs")


if __name__ == "__main__":
    main()
