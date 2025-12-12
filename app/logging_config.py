import logging
import logging.config
import json
import re
import sys
from typing import Dict, Any, List, Pattern
from app.config import settings
from app.context import get_request_id


class SensitiveDataFilter(logging.Filter):
    """Filter that masks sensitive data in log messages.
    
    Automatically redacts passwords, tokens, keys, and other sensitive
    information from log messages to prevent accidental exposure.
    """
    
    # Patterns to match sensitive data
    SENSITIVE_PATTERNS: List[tuple[Pattern, str]] = [
        # Passwords in various formats
        (re.compile(r'(password|passwd|pwd)\s*[=:]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1=***REDACTED***'),
        (re.compile(r'"password"\s*:\s*"[^"]*"', re.IGNORECASE), '"password": "***REDACTED***"'),
        
        # API keys and tokens
        (re.compile(r'(api[_-]?key|apikey)\s*[=:]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1=***REDACTED***'),
        (re.compile(r'(auth[_-]?token|token|bearer)\s*[=:]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1=***REDACTED***'),
        (re.compile(r'Authorization:\s*(Bearer\s+)?[^\s]+', re.IGNORECASE), 'Authorization: ***REDACTED***'),
        
        # Secret keys
        (re.compile(r'(secret[_-]?key|secret)\s*[=:]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1=***REDACTED***'),
        (re.compile(r'(encryption[_-]?key)\s*[=:]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1=***REDACTED***'),
        
        # SMTP credentials
        (re.compile(r'(smtp[_-]?pass|smtp[_-]?password)\s*[=:]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1=***REDACTED***'),
        
        # Twilio credentials
        (re.compile(r'(twilio[_-]?auth[_-]?token)\s*[=:]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1=***REDACTED***'),
        (re.compile(r'(account[_-]?sid)\s*[=:]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'\1=***REDACTED***'),
        
        # Database credentials in URLs
        (re.compile(r'(://[^:]+:)([^@]+)(@)', re.IGNORECASE), r'\1***REDACTED***\3'),
        
        # Credit card numbers (basic pattern)
        (re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'), '***CARD-REDACTED***'),
        
        # Email addresses in sensitive contexts
        (re.compile(r'(email[_-]?from|from[_-]?email)\s*[=:]\s*["\']?([^"\'\s,}@]+@[^"\'\s,}]+)', re.IGNORECASE), r'\1=***EMAIL-REDACTED***'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and mask sensitive data in the log record.
        
        Args:
            record: The log record to filter
            
        Returns:
            bool: Always True (we modify but don't drop records)
        """
        # Mask the message
        if record.msg:
            record.msg = self._mask_sensitive_data(str(record.msg))
        
        # Mask args if they're strings
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._mask_sensitive_data(str(v)) if isinstance(v, str) else v 
                              for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._mask_sensitive_data(str(arg)) if isinstance(arg, str) else arg 
                    for arg in record.args
                )
        
        return True
    
    def _mask_sensitive_data(self, text: str) -> str:
        """Apply all sensitive data patterns to mask the text.
        
        Args:
            text: The text to mask
            
        Returns:
            str: The masked text
        """
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            text = pattern.sub(replacement, text)
        return text


class RequestIDFilter(logging.Filter):
    """Filter that adds request ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request ID to the log record.
        
        Args:
            record: The log record
            
        Returns:
            bool: Always True
        """
        record.request_id = get_request_id() or "-"
        return True


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Get request ID from context
        request_id = get_request_id()
        
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request ID if available
        if request_id:
            log_entry["request_id"] = request_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "exc_info", "exc_text", "stack_info",
                          "lineno", "funcName", "created", "msecs", "relativeCreated",
                          "thread", "threadName", "processName", "process", "getMessage",
                          "request_id"]:
                log_entry[key] = value
        
        return json.dumps(log_entry)


def setup_logging() -> None:
    """Setup application logging configuration."""
    
    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure logging
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "sensitive_data": {
                "()": SensitiveDataFilter,
            },
            "request_id": {
                "()": RequestIDFilter,
            },
        },
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "json" if settings.log_format == "json" else "standard",
                "filters": ["sensitive_data", "request_id"],
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "json" if settings.log_format == "json" else "standard",
                "filters": ["sensitive_data", "request_id"],
                "filename": "app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": logging.INFO,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": logging.INFO,
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }
    
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f"app.{name}")


# Setup logging on import
setup_logging()
