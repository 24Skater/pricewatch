"""Custom exception classes for the application."""

from typing import Optional, Dict, Any

__all__ = [
    "PricewatchException",
    "ValidationError",
    "SecurityError",
    "ScrapingError",
    "NotificationError",
    "DatabaseError",
    "ConfigurationError",
    "RateLimitError",
]


class PricewatchException(Exception):
    """Base exception for Pricewatch application.
    
    All custom exceptions inherit from this class to provide
    consistent error handling with machine-readable codes.
    
    Attributes:
        message: Human-readable error message
        code: Machine-readable error code (e.g., "VALIDATION_ERROR")
        details: Additional context about the error
    """
    
    default_code: str = "PRICEWATCH_ERROR"
    
    def __init__(
        self,
        message: str = "An error occurred",
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code or self.default_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.message,
            "code": self.code,
            "details": self.details
        }


class ValidationError(PricewatchException):
    """Raised when input validation fails."""
    default_code = "VALIDATION_ERROR"


class SecurityError(PricewatchException):
    """Raised when security validation fails."""
    default_code = "SECURITY_ERROR"


class ScrapingError(PricewatchException):
    """Raised when web scraping fails."""
    default_code = "SCRAPING_ERROR"


class NotificationError(PricewatchException):
    """Raised when notification sending fails."""
    default_code = "NOTIFICATION_ERROR"


class DatabaseError(PricewatchException):
    """Raised when database operations fail."""
    default_code = "DATABASE_ERROR"


class ConfigurationError(PricewatchException):
    """Raised when configuration is invalid."""
    default_code = "CONFIGURATION_ERROR"


class RateLimitError(PricewatchException):
    """Raised when rate limit is exceeded."""
    default_code = "RATE_LIMIT_ERROR"
