import logging
import logging.config
import json
import sys
from typing import Dict, Any
from app.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "exc_info", "exc_text", "stack_info",
                          "lineno", "funcName", "created", "msecs", "relativeCreated",
                          "thread", "threadName", "processName", "process", "getMessage"]:
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
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "json" if settings.log_format == "json" else "standard",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "json" if settings.log_format == "json" else "standard",
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
