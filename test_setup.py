#!/usr/bin/env python3
"""
Test script to verify Pricewatch v2.0 setup is working correctly.
Run this after setting up the application to verify everything is working.
"""

import requests
import json
import sys
import time
from pathlib import Path


def test_health_endpoint():
    """Test basic health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_detailed_health():
    """Test detailed health endpoint."""
    print("🔍 Testing detailed health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health/detailed", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Detailed health check passed")
            print(f"   Overall status: {data.get('overall_status', 'unknown')}")
            print(f"   Environment: {data.get('environment', 'unknown')}")
            return True
        else:
            print(f"❌ Detailed health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Detailed health check failed: {e}")
        return False


def test_metrics_endpoint():
    """Test metrics endpoint."""
    print("🔍 Testing metrics endpoint...")
    try:
        response = requests.get("http://localhost:8000/metrics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Metrics endpoint working")
            return True
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Metrics endpoint failed: {e}")
        return False


def test_api_docs():
    """Test API documentation endpoint."""
    print("🔍 Testing API documentation...")
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API documentation accessible")
            return True
        else:
            print(f"❌ API documentation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API documentation failed: {e}")
        return False


def test_main_page():
    """Test main application page."""
    print("🔍 Testing main application page...")
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Main application page accessible")
            return True
        else:
            print(f"❌ Main application page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Main application page failed: {e}")
        return False


def test_database_file():
    """Test if database file exists."""
    print("🔍 Testing database file...")
    db_file = Path("pricewatch.db")
    if db_file.exists():
        print("✅ Database file exists")
        return True
    else:
        print("❌ Database file not found")
        return False


def test_log_file():
    """Test if log file exists."""
    print("🔍 Testing log file...")
    log_file = Path("app.log")
    if log_file.exists():
        print("✅ Log file exists")
        return True
    else:
        print("⚠️  Log file not found (may be normal if no logs generated yet)")
        return True


def test_environment_file():
    """Test if environment file exists."""
    print("🔍 Testing environment file...")
    env_file = Path(".env")
    if env_file.exists():
        print("✅ Environment file exists")
        return True
    else:
        print("❌ Environment file not found")
        return False


def test_requirements_file():
    """Test if requirements file exists."""
    print("🔍 Testing requirements file...")
    req_file = Path("requirements.txt")
    if req_file.exists():
        print("✅ Requirements file exists")
        return True
    else:
        print("❌ Requirements file not found")
        return False


def test_config_file():
    """Test if config file exists."""
    print("🔍 Testing config file...")
    config_file = Path("app/config.py")
    if config_file.exists():
        print("✅ Config file exists")
        return True
    else:
        print("❌ Config file not found")
        return False


def main():
    """Run all tests."""
    print("🚀 Pricewatch v2.0 Setup Test")
    print("=" * 50)
    
    tests = [
        ("Environment File", test_environment_file),
        ("Requirements File", test_requirements_file),
        ("Config File", test_config_file),
        ("Database File", test_database_file),
        ("Log File", test_log_file),
        ("Health Endpoint", test_health_endpoint),
        ("Detailed Health", test_detailed_health),
        ("Metrics Endpoint", test_metrics_endpoint),
        ("API Documentation", test_api_docs),
        ("Main Application", test_main_page),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"   ⚠️  {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is working correctly.")
        print("\n✅ You can now:")
        print("   - Visit http://localhost:8000 to use the application")
        print("   - Visit http://localhost:8000/docs for API documentation")
        print("   - Check http://localhost:8000/health for health status")
        print("   - View app.log for application logs")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Make sure the application is running (uvicorn app.main:app --reload)")
        print("   2. Check that all dependencies are installed (pip install -r requirements.txt)")
        print("   3. Verify your .env file is configured correctly")
        print("   4. Check the application logs for errors")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
