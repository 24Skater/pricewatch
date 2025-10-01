#!/usr/bin/env python3
"""
Setup script for Pricewatch v2.0 improvements.
This script helps initialize the improved application.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def create_env_file():
    """Create .env file from example if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from example...")
        env_file.write_text(env_example.read_text())
        print("✅ .env file created")
    elif not env_file.exists():
        print("⚠️  No .env.example found, creating basic .env file...")
        basic_env = """# Pricewatch Configuration
SECRET_KEY=your-secret-key-change-in-production-minimum-32-characters
DATABASE_URL=sqlite:///pricewatch.db
ENVIRONMENT=development
LOG_LEVEL=INFO
LOG_FORMAT=json
"""
        env_file.write_text(basic_env)
        print("✅ Basic .env file created")


def setup_database_migrations():
    """Initialize Alembic for database migrations."""
    print("🗄️  Setting up database migrations...")
    
    # Check if alembic.ini exists
    if not Path("alembic.ini").exists():
        print("❌ alembic.ini not found. Please ensure it exists.")
        return False
    
    # Initialize migrations if they don't exist
    if not Path("migrations").exists():
        if not run_command("alembic init migrations", "Initializing Alembic"):
            return False
    
    # Create initial migration
    if not run_command("alembic revision --autogenerate -m 'Initial migration'", "Creating initial migration"):
        return False
    
    # Apply migrations
    if not run_command("alembic upgrade head", "Applying database migrations"):
        return False
    
    return True


def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    return True


def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    
    if not run_command("python -m pytest tests/ -v", "Running test suite"):
        print("⚠️  Some tests failed, but continuing...")
        return True
    
    return True


def main():
    """Main setup function."""
    print("🚀 Setting up Pricewatch v2.0 improvements...")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Setup database migrations
    if not setup_database_migrations():
        print("❌ Failed to setup database migrations")
        sys.exit(1)
    
    # Run tests
    run_tests()
    
    print("=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update .env file with your configuration")
    print("2. Set a secure SECRET_KEY (minimum 32 characters)")
    print("3. Configure SMTP/Twilio credentials if needed")
    print("4. Run the application: uvicorn app.main:app --reload")
    print("\n🔗 Useful endpoints:")
    print("- http://localhost:8000/ - Main application")
    print("- http://localhost:8000/health - Health check")
    print("- http://localhost:8000/health/detailed - Detailed health")
    print("- http://localhost:8000/docs - API documentation")


if __name__ == "__main__":
    main()
