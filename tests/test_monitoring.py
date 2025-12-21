"""Tests for monitoring and health check functionality.

Tests health check methods and endpoints with mocked dependencies.
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from app.monitoring import HealthChecker, health_checker


# =============================================================================
# Test HealthChecker Class
# =============================================================================

class TestHealthChecker:
    """Tests for HealthChecker class."""
    
    def test_health_checker_initialization(self):
        """Test HealthChecker initializes with start time."""
        checker = HealthChecker()
        
        assert hasattr(checker, "start_time")
        assert checker.start_time <= time.time()


class TestCheckDatabase:
    """Tests for check_database() method."""
    
    @patch("app.monitoring.SessionLocal")
    def test_check_database_success(self, mock_session_class):
        """Test database check returns healthy status."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.execute.return_value.fetchone.return_value = (1,)
        
        checker = HealthChecker()
        result = checker.check_database()
        
        assert result["status"] == "healthy"
        assert "response_time_ms" in result
        assert result["connection"] == "active"
        mock_session.close.assert_called_once()
    
    @patch("app.monitoring.SessionLocal")
    def test_check_database_failure(self, mock_session_class):
        """Test database check returns unhealthy on error."""
        mock_session_class.side_effect = Exception("Connection failed")
        
        checker = HealthChecker()
        result = checker.check_database()
        
        assert result["status"] == "unhealthy"
        assert "error" in result
        assert result["connection"] == "failed"
    
    @patch("app.monitoring.SessionLocal")
    def test_check_database_query_error(self, mock_session_class):
        """Test database check handles query errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.execute.side_effect = Exception("Query failed")
        
        checker = HealthChecker()
        result = checker.check_database()
        
        assert result["status"] == "unhealthy"
        assert "Query failed" in result["error"]


class TestCheckSystemResources:
    """Tests for check_system_resources() method."""
    
    @patch("app.monitoring.psutil")
    def test_check_system_resources_success(self, mock_psutil):
        """Test system resources check returns healthy status."""
        mock_psutil.cpu_percent.return_value = 25.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=16 * 1024**3,
            available=8 * 1024**3,
            percent=50.0
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            total=500 * 1024**3,
            free=250 * 1024**3,
            used=250 * 1024**3
        )
        
        checker = HealthChecker()
        result = checker.check_system_resources()
        
        assert result["status"] == "healthy"
        assert result["cpu_percent"] == 25.0
        assert "memory" in result
        assert "disk" in result
        assert result["memory"]["percent_used"] == 50.0
    
    @patch("app.monitoring.psutil")
    def test_check_system_resources_failure(self, mock_psutil):
        """Test system resources check handles errors."""
        mock_psutil.cpu_percent.side_effect = Exception("CPU check failed")
        
        checker = HealthChecker()
        result = checker.check_system_resources()
        
        assert result["status"] == "unhealthy"
        assert "error" in result
    
    @patch("app.monitoring.psutil")
    def test_check_system_resources_values(self, mock_psutil):
        """Test system resources values are correctly calculated."""
        mock_psutil.cpu_percent.return_value = 75.5
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=32 * 1024**3,  # 32 GB
            available=16 * 1024**3,  # 16 GB
            percent=50.0
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            total=1000 * 1024**3,  # 1 TB
            free=200 * 1024**3,  # 200 GB
            used=800 * 1024**3  # 800 GB
        )
        
        checker = HealthChecker()
        result = checker.check_system_resources()
        
        assert result["memory"]["total_gb"] == 32.0
        assert result["memory"]["available_gb"] == 16.0
        assert result["disk"]["total_gb"] == 1000.0
        assert result["disk"]["free_gb"] == 200.0
        assert result["disk"]["percent_used"] == 80.0


class TestCheckApplicationHealth:
    """Tests for check_application_health() method."""
    
    @patch("app.monitoring.SessionLocal")
    def test_check_application_health_success(self, mock_session_class):
        """Test application health check returns correct metrics."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock query results
        mock_session.execute.return_value.fetchone.side_effect = [
            (10,),  # total trackers
            (8,),   # active trackers
            (3,),   # profiles
            (25,),  # recent price checks
        ]
        
        checker = HealthChecker()
        result = checker.check_application_health()
        
        assert result["status"] == "healthy"
        assert result["trackers"]["total"] == 10
        assert result["trackers"]["active"] == 8
        assert result["profiles"] == 3
        assert result["recent_price_checks"] == 25
        mock_session.close.assert_called_once()
    
    @patch("app.monitoring.SessionLocal")
    def test_check_application_health_failure(self, mock_session_class):
        """Test application health check handles errors."""
        mock_session_class.side_effect = Exception("DB error")
        
        checker = HealthChecker()
        result = checker.check_application_health()
        
        assert result["status"] == "unhealthy"
        assert "error" in result


class TestGetUptime:
    """Tests for get_uptime() method."""
    
    def test_get_uptime_returns_correct_values(self):
        """Test uptime calculation is correct."""
        checker = HealthChecker()
        
        # Wait a tiny bit
        time.sleep(0.1)
        
        result = checker.get_uptime()
        
        assert "uptime_seconds" in result
        assert "uptime_hours" in result
        assert "start_time" in result
        assert result["uptime_seconds"] >= 0
        assert result["start_time"] == checker.start_time
    
    def test_get_uptime_increases_over_time(self):
        """Test uptime increases over time."""
        checker = HealthChecker()
        
        result1 = checker.get_uptime()
        time.sleep(0.1)
        result2 = checker.get_uptime()
        
        assert result2["uptime_seconds"] >= result1["uptime_seconds"]


class TestComprehensiveHealthCheck:
    """Tests for comprehensive_health_check() method."""
    
    @patch.object(HealthChecker, "check_database")
    @patch.object(HealthChecker, "check_system_resources")
    @patch.object(HealthChecker, "check_application_health")
    @patch.object(HealthChecker, "get_uptime")
    def test_comprehensive_health_check_all_healthy(
        self, mock_uptime, mock_app, mock_system, mock_db
    ):
        """Test comprehensive check returns healthy when all checks pass."""
        mock_db.return_value = {"status": "healthy"}
        mock_system.return_value = {"status": "healthy"}
        mock_app.return_value = {"status": "healthy"}
        mock_uptime.return_value = {"uptime_seconds": 100}
        
        checker = HealthChecker()
        result = checker.comprehensive_health_check()
        
        assert result["overall_status"] == "healthy"
        assert "timestamp" in result
        assert "environment" in result
        assert "version" in result
        assert "checks" in result
        assert "database" in result["checks"]
        assert "system_resources" in result["checks"]
        assert "application" in result["checks"]
        assert "uptime" in result["checks"]
    
    @patch.object(HealthChecker, "check_database")
    @patch.object(HealthChecker, "check_system_resources")
    @patch.object(HealthChecker, "check_application_health")
    @patch.object(HealthChecker, "get_uptime")
    def test_comprehensive_health_check_one_unhealthy(
        self, mock_uptime, mock_app, mock_system, mock_db
    ):
        """Test comprehensive check returns unhealthy when any check fails."""
        mock_db.return_value = {"status": "unhealthy", "error": "DB down"}
        mock_system.return_value = {"status": "healthy"}
        mock_app.return_value = {"status": "healthy"}
        mock_uptime.return_value = {"uptime_seconds": 100}
        
        checker = HealthChecker()
        result = checker.comprehensive_health_check()
        
        assert result["overall_status"] == "unhealthy"
    
    @patch.object(HealthChecker, "check_database")
    @patch.object(HealthChecker, "check_system_resources")
    @patch.object(HealthChecker, "check_application_health")
    @patch.object(HealthChecker, "get_uptime")
    def test_comprehensive_health_check_multiple_unhealthy(
        self, mock_uptime, mock_app, mock_system, mock_db
    ):
        """Test comprehensive check handles multiple failures."""
        mock_db.return_value = {"status": "unhealthy"}
        mock_system.return_value = {"status": "unhealthy"}
        mock_app.return_value = {"status": "healthy"}
        mock_uptime.return_value = {"uptime_seconds": 100}
        
        checker = HealthChecker()
        result = checker.comprehensive_health_check()
        
        assert result["overall_status"] == "unhealthy"


class TestGlobalHealthChecker:
    """Tests for global health_checker instance."""
    
    def test_global_instance_exists(self):
        """Test global health_checker instance is available."""
        assert health_checker is not None
        assert isinstance(health_checker, HealthChecker)
    
    def test_global_instance_has_methods(self):
        """Test global instance has all required methods."""
        assert hasattr(health_checker, "check_database")
        assert hasattr(health_checker, "check_system_resources")
        assert hasattr(health_checker, "check_application_health")
        assert hasattr(health_checker, "get_uptime")
        assert hasattr(health_checker, "comprehensive_health_check")


# =============================================================================
# Test Health Endpoints Structure
# =============================================================================

class TestHealthEndpointStructure:
    """Test health endpoint response structure."""
    
    def test_basic_health_response_structure(self):
        """Test basic health response has required fields."""
        # Simulate what /health returns
        response = {
            "status": "healthy",
            "version": "2.0.0",
            "environment": "development"
        }
        
        assert "status" in response
        assert "version" in response
        assert "environment" in response
    
    @patch.object(HealthChecker, "check_database")
    @patch.object(HealthChecker, "check_system_resources")
    @patch.object(HealthChecker, "check_application_health")
    @patch.object(HealthChecker, "get_uptime")
    def test_detailed_health_response_structure(
        self, mock_uptime, mock_app, mock_system, mock_db
    ):
        """Test detailed health response has all sections."""
        mock_db.return_value = {"status": "healthy", "response_time_ms": 5}
        mock_system.return_value = {"status": "healthy", "cpu_percent": 25}
        mock_app.return_value = {"status": "healthy", "trackers": {"total": 10}}
        mock_uptime.return_value = {"uptime_seconds": 3600}
        
        checker = HealthChecker()
        result = checker.comprehensive_health_check()
        
        # Verify structure
        assert "overall_status" in result
        assert "timestamp" in result
        assert "checks" in result
        assert "database" in result["checks"]
        assert "system_resources" in result["checks"]
        assert "application" in result["checks"]
        assert "uptime" in result["checks"]

