#!/usr/bin/env python3
"""
Retry migration creation after fixing env.py
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        # Split the command properly for subprocess
        cmd_parts = command.split()
        result = subprocess.run(cmd_parts, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def main():
    """Retry migration creation."""
    print("🔄 Retrying migration creation...")
    
    # Create initial migration
    if not run_command(".venv\\Scripts\\alembic revision --autogenerate -m 'Initial migration'", "Creating initial migration"):
        return False
    
    # Apply migrations
    if not run_command(".venv\\Scripts\\alembic upgrade head", "Applying migrations"):
        return False
    
    print("✅ Migration creation completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
