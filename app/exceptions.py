"""Custom exception classes for the application."""


class PricewatchException(Exception):
    """Base exception for Pricewatch application."""
    pass


class ValidationError(PricewatchException):
    """Raised when input validation fails."""
    pass


class SecurityError(PricewatchException):
    """Raised when security validation fails."""
    pass


class ScrapingError(PricewatchException):
    """Raised when web scraping fails."""
    pass


class NotificationError(PricewatchException):
    """Raised when notification sending fails."""
    pass


class DatabaseError(PricewatchException):
    """Raised when database operations fail."""
    pass


class ConfigurationError(PricewatchException):
    """Raised when configuration is invalid."""
    pass


class RateLimitError(PricewatchException):
    """Raised when rate limit is exceeded."""
    pass
