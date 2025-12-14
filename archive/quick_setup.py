#!/usr/bin/env python3
"""
Quick setup script for Pricewatch v2.0 on a new PC.
This script automates the setup process and tests the application.
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def run_command(command, description, check=True):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            return True
        else:
            print(f"⚠️  {description} completed with warnings: {result.stderr}")
            return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
        return True


def create_virtual_environment():
    """Create virtual environment."""
    if not Path(".venv").exists():
        return run_command("python -m venv .venv", "Creating virtual environment")
    else:
        print("✅ Virtual environment already exists")
        return True


def activate_virtual_environment():
    """Activate virtual environment."""
    if os.name == 'nt':  # Windows
        activate_script = ".venv\\Scripts\\activate"
    else:  # macOS/Linux
        activate_script = "source .venv/bin/activate"
    
    print(f"🔄 Activating virtual environment...")
    print(f"   Run: {activate_script}")
    return True


def install_dependencies():
    """Install required dependencies."""
    if os.name == 'nt':  # Windows
        pip_cmd = ".venv\\Scripts\\pip"
    else:  # macOS/Linux
        pip_cmd = ".venv/bin/pip"
    
    return run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies")


def create_env_file():
    """Create .env file if it doesn't exist."""
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
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
        return True
    else:
        print("✅ .env file already exists")
        return True


def setup_database():
    """Setup database with migrations."""
    print("🗄️  Setting up database...")
    
    # Check if alembic.ini exists
    if not Path("alembic.ini").exists():
        print("❌ alembic.ini not found. Please ensure it exists.")
        return False
    
    # Determine the correct alembic command path
    if os.name == 'nt':  # Windows
        alembic_cmd = ".venv\\Scripts\\alembic"
    else:  # macOS/Linux
        alembic_cmd = ".venv/bin/alembic"
    
    # Initialize migrations if they don't exist
    if not Path("migrations").exists():
        if not run_command(f"{alembic_cmd} init migrations", "Initializing Alembic"):
            return False
    
    # Create initial migration
    if not run_command(f"{alembic_cmd} revision --autogenerate -m 'Initial migration'", "Creating initial migration"):
        return False
    
    # Apply migrations
    if not run_command(f"{alembic_cmd} upgrade head", "Applying database migrations"):
        return False
    
    return True


def start_application():
    """Start the application in the background."""
    print("🚀 Starting application...")
    
    if os.name == 'nt':  # Windows
        uvicorn_cmd = ".venv\\Scripts\\uvicorn"
    else:  # macOS/Linux
        uvicorn_cmd = ".venv/bin/uvicorn"
    
    # Start application in background
    try:
        process = subprocess.Popen([
            uvicorn_cmd, "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for the application to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Application started successfully")
            return process
        else:
            print("❌ Application failed to start")
            return None
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        return None


def test_application():
    """Test if the application is working."""
    print("🧪 Testing application...")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Application is responding")
            return True
        else:
            print(f"❌ Application health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Application test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Pricewatch v2.0 Quick Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        print("❌ Failed to create virtual environment")
        sys.exit(1)
    
    # Activate virtual environment
    activate_virtual_environment()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("❌ Failed to create .env file")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("❌ Failed to setup database")
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
