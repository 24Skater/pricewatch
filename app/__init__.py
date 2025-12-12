"""Pricewatch - Enterprise Price Tracking Application.

A modern, secure price monitoring tool with email/SMS notifications.
"""

__version__ = "2.1.0"
__author__ = "Pricewatch Team"
__all__ = ["app", "settings", "get_db"]

from app.config import settings
from app.database import get_db
from app.main import app

