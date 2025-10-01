"""Monitoring and health check functionality."""

import time
import psutil
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.logging_config import get_logger
from app.config import settings

logger = get_logger(__name__)


class HealthChecker:
    """Health check functionality."""
    
    def __init__(self):
        self.start_time = time.time()
    
    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            db = SessionLocal()
            start_time = time.time()
            
            # Test basic connectivity
            result = db.execute(text("SELECT 1")).fetchone()
            
            # Test query performance
            db.execute(text("SELECT COUNT(*) FROM trackers")).fetchone()
            
            response_time = time.time() - start_time
            
            db.close()
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "connection": "active"
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent_used": round((disk.used / disk.total) * 100, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"System resources check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_application_health(self) -> Dict[str, Any]:
        """Check application-specific health metrics."""
        try:
            db = SessionLocal()
            
            # Get tracker statistics
            tracker_count = db.execute(text("SELECT COUNT(*) FROM trackers")).fetchone()[0]
            active_trackers = db.execute(
                text("SELECT COUNT(*) FROM trackers WHERE is_active = 1")
            ).fetchone()[0]
            
            # Get profile count
            profile_count = db.execute(text("SELECT COUNT(*) FROM notification_profiles")).fetchone()[0]
            
            # Get recent price history
            recent_prices = db.execute(
                text("SELECT COUNT(*) FROM price_history WHERE checked_at > datetime('now', '-1 hour')")
            ).fetchone()[0]
            
            db.close()
            
            return {
                "status": "healthy",
                "trackers": {
                    "total": tracker_count,
                    "active": active_trackers
                },
                "profiles": profile_count,
                "recent_price_checks": recent_prices
            }
            
        except Exception as e:
            logger.error(f"Application health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_uptime(self) -> Dict[str, Any]:
        """Get application uptime information."""
        uptime_seconds = time.time() - self.start_time
        
        return {
            "uptime_seconds": int(uptime_seconds),
            "uptime_hours": round(uptime_seconds / 3600, 2),
            "start_time": self.start_time
        }
    
    def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        logger.info("Performing comprehensive health check")
        
        checks = {
            "database": self.check_database(),
            "system_resources": self.check_system_resources(),
            "application": self.check_application_health(),
            "uptime": self.get_uptime()
        }
        
        # Determine overall health
        overall_status = "healthy"
        for check_name, check_result in checks.items():
            if check_result.get("status") == "unhealthy":
                overall_status = "unhealthy"
                break
        
        return {
            "overall_status": overall_status,
            "timestamp": time.time(),
            "environment": settings.environment,
            "version": "2.0.0",
            "checks": checks
        }


# Global health checker instance
health_checker = HealthChecker()
