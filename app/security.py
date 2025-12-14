"""Security utilities for input validation, encryption, and rate limiting."""

import os
import re
import secrets
import hashlib
import logging
import time
import ipaddress
import socket
from typing import Optional
from urllib.parse import urlparse
from cryptography.fernet import Fernet
from app.config import settings
from app.exceptions import SecurityError

__all__ = [
    "is_private_ip",
    "is_ip_address",
    "InputValidator",
    "EncryptionService",
    "RateLimiter",
    "input_validator",
    "encryption_service",
    "rate_limiter",
]

logger = logging.getLogger("app.security")


def is_private_ip(ip_str: str) -> bool:
    """Check if an IP address is private, loopback, or otherwise internal.
    
    Checks for:
    - 10.0.0.0/8 (private)
    - 172.16.0.0/12 (private)
    - 192.168.0.0/16 (private)
    - 127.0.0.0/8 (loopback)
    - 169.254.0.0/16 (link-local)
    - ::1 (IPv6 loopback)
    - fc00::/7 (IPv6 private)
    - fe80::/10 (IPv6 link-local)
    
    Args:
        ip_str: The IP address string to check
        
    Returns:
        bool: True if the IP is private/internal, False otherwise
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        
        # Check for private, loopback, link-local, or reserved addresses
        return (
            ip.is_private or
            ip.is_loopback or
            ip.is_link_local or
            ip.is_reserved or
            ip.is_multicast or
            ip.is_unspecified
        )
    except ValueError:
        # Invalid IP address format
        return False


def is_ip_address(hostname: str) -> bool:
    """Check if a hostname is an IP address (v4 or v6).
    
    Args:
        hostname: The hostname to check
        
    Returns:
        bool: True if hostname is an IP address
    """
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


class InputValidator:
    """Input validation utilities with comprehensive security checks."""
    
    # Allowed URL schemes
    ALLOWED_SCHEMES = ['http', 'https']
    
    # Known localhost hostnames
    LOCALHOST_HOSTNAMES = [
        'localhost',
        'localhost.localdomain',
        'local',
        '127.0.0.1',
        '0.0.0.0',  # nosec B104 - This is for SSRF protection checking, not binding
        '::1',
        '[::1]',
    ]
    
    @staticmethod
    def validate_url(url: str, allow_private: bool = None) -> bool:
        """Validate URL format and security, with SSRF protection.
        
        Args:
            url: The URL to validate
            allow_private: Whether to allow private/internal IPs.
                          If None, only allowed in development mode.
        
        Returns:
            bool: True if URL is valid and safe
        """
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                logger.warning(f"URL validation failed: missing scheme or netloc - {url[:100]}")
                return False
            
            # Check for allowed schemes only
            if parsed.scheme.lower() not in InputValidator.ALLOWED_SCHEMES:
                logger.warning(f"URL validation failed: disallowed scheme '{parsed.scheme}'")
                return False
            
            hostname = parsed.hostname
            if not hostname:
                logger.warning(f"URL validation failed: no hostname - {url[:100]}")
                return False
            
            # Determine if private IPs should be allowed
            if allow_private is None:
                allow_private = settings.environment == "development"
            
            # Check for localhost hostnames
            if hostname.lower() in InputValidator.LOCALHOST_HOSTNAMES:
                if not allow_private:
                    logger.warning(
                        f"SSRF protection: blocked localhost hostname '{hostname}' "
                        f"in {settings.environment} mode"
                    )
                    return False
            
            # Check if hostname is an IP address
            if is_ip_address(hostname):
                # Check if it's a private IP
                if is_private_ip(hostname):
                    if not allow_private:
                        logger.warning(
                            f"SSRF protection: blocked private IP '{hostname}' "
                            f"in {settings.environment} mode"
                        )
                        return False
                # In non-development, block direct IP access entirely
                elif settings.environment != "development":
                    logger.warning(
                        f"SSRF protection: blocked direct IP access '{hostname}' "
                        f"in {settings.environment} mode"
                    )
                    return False
            else:
                # For hostnames, try to resolve and check the IP
                # Only in non-development environments
                if settings.environment != "development":
                    try:
                        resolved_ips = socket.getaddrinfo(hostname, None)
                        for result in resolved_ips:
                            ip = result[4][0]
                            if is_private_ip(ip):
                                logger.warning(
                                    f"SSRF protection: hostname '{hostname}' resolves to "
                                    f"private IP '{ip}' in {settings.environment} mode"
                                )
                                return False
                    except socket.gaierror:
                        # DNS resolution failed - let it pass, will fail at request time
                        pass
            
            return True
            
        except Exception as e:
            logger.warning(f"URL validation failed with exception: {e}")
            return False
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate phone number format.
        
        Args:
            phone: The phone number to validate
            
        Returns:
            bool: True if valid phone number format
        """
        if not phone:
            return False
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        return 10 <= len(digits) <= 15
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format.
        
        Args:
            email: The email address to validate
            
        Returns:
            bool: True if valid email format
        """
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent XSS.
        
        Args:
            text: The text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            str: Sanitized text
        """
        if not text:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', text)
        
        # Limit length
        return sanitized[:max_length].strip()


class EncryptionService:
    """Service for encrypting/decrypting sensitive data.
    
    Reads encryption key from ENCRYPTION_KEY environment variable.
    In development mode, generates a temporary key if not set (with warning).
    In production mode, requires ENCRYPTION_KEY to be set.
    """
    
    _dev_key: Optional[bytes] = None  # Class-level cache for dev key
    
    def __init__(self):
        self._key = self._get_key()
        self._cipher = Fernet(self._key)
    
    def _get_key(self) -> bytes:
        """Get encryption key from environment or generate for development.
        
        Returns:
            bytes: The Fernet encryption key
            
        Raises:
            SecurityError: If key is not set in production environment
        """
        # First, try to get key from settings (environment variable)
        if settings.encryption_key:
            key = settings.encryption_key
            if isinstance(key, str):
                return key.encode()
            return key
        
        # No key set - handle based on environment
        if settings.environment == "production":
            raise SecurityError(
                "ENCRYPTION_KEY environment variable must be set in production. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        
        # Development/staging: generate a temporary key (cached at class level)
        if EncryptionService._dev_key is None:
            EncryptionService._dev_key = Fernet.generate_key()
            logger.warning(
                "⚠️  ENCRYPTION_KEY not set - using auto-generated key for development. "
                "Data encrypted with this key will be unreadable after restart. "
                "Set ENCRYPTION_KEY environment variable for persistence."
            )
        
        return EncryptionService._dev_key
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data.
        
        Args:
            data: The plaintext string to encrypt
            
        Returns:
            str: The encrypted data as a string, or empty string if data is empty
        """
        if not data:
            return ""
        return self._cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data.
        
        Args:
            encrypted_data: The encrypted string to decrypt
            
        Returns:
            str: The decrypted plaintext, or empty string if data is empty
        """
        if not encrypted_data:
            return ""
        return self._cipher.decrypt(encrypted_data.encode()).decode()


class RateLimiter:
    """Simple in-memory rate limiter with automatic cleanup.
    
    Features:
    - Per-identifier rate limiting with configurable window
    - Automatic cleanup of expired entries to prevent memory leaks
    - Maximum entries limit with oldest-first eviction
    """
    
    # Configuration constants
    CLEANUP_INTERVAL = 300  # Cleanup every 5 minutes
    MAX_ENTRIES = 10000  # Maximum number of identifiers to track
    DEFAULT_WINDOW = 60  # Default window in seconds
    
    def __init__(self):
        self._requests: dict[str, list[float]] = {}
        self._last_cleanup = time.time()
        self._first_seen: dict[str, float] = {}  # Track when each identifier was first seen
    
    def is_allowed(self, identifier: str, limit: int, window: int = DEFAULT_WINDOW) -> bool:
        """Check if request is allowed based on rate limit.
        
        Args:
            identifier: Unique identifier (usually IP address)
            limit: Maximum number of requests allowed in window
            window: Time window in seconds
            
        Returns:
            bool: True if request is allowed, False if rate limited
        """
        now = time.time()
        
        # Periodic cleanup of stale entries
        self._maybe_cleanup(window)
        
        # Initialize if new identifier
        if identifier not in self._requests:
            # Check if we need to evict old entries
            self._maybe_evict()
            self._requests[identifier] = []
            self._first_seen[identifier] = now
        
        # Clean old requests for this identifier
        self._requests[identifier] = [
            req_time for req_time in self._requests[identifier]
            if now - req_time < window
        ]
        
        # Check limit
        if len(self._requests[identifier]) >= limit:
            return False
        
        # Add current request
        self._requests[identifier].append(now)
        return True
    
    def _maybe_cleanup(self, window: int) -> None:
        """Cleanup expired entries if cleanup interval has passed.
        
        Args:
            window: The rate limit window to use for determining expired entries
        """
        now = time.time()
        
        # Only cleanup periodically
        if now - self._last_cleanup < self.CLEANUP_INTERVAL:
            return
        
        self._last_cleanup = now
        expired_identifiers = []
        
        # Find identifiers with no recent requests
        for identifier, requests in self._requests.items():
            # Remove old requests
            active_requests = [t for t in requests if now - t < window]
            
            if not active_requests:
                expired_identifiers.append(identifier)
            else:
                self._requests[identifier] = active_requests
        
        # Remove expired identifiers
        for identifier in expired_identifiers:
            del self._requests[identifier]
            if identifier in self._first_seen:
                del self._first_seen[identifier]
        
        if expired_identifiers:
            logger.debug(f"Rate limiter cleanup: removed {len(expired_identifiers)} stale entries")
    
    def _maybe_evict(self) -> None:
        """Evict oldest entries if we've reached the maximum limit."""
        if len(self._requests) < self.MAX_ENTRIES:
            return
        
        # Sort identifiers by first seen time (oldest first)
        sorted_identifiers = sorted(
            self._first_seen.items(),
            key=lambda x: x[1]
        )
        
        # Remove oldest 10% of entries
        num_to_remove = max(1, len(sorted_identifiers) // 10)
        for identifier, _ in sorted_identifiers[:num_to_remove]:
            if identifier in self._requests:
                del self._requests[identifier]
            if identifier in self._first_seen:
                del self._first_seen[identifier]
        
        logger.warning(
            f"Rate limiter eviction: removed {num_to_remove} oldest entries "
            f"(max {self.MAX_ENTRIES} reached)"
        )
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics for monitoring.
        
        Returns:
            dict: Statistics about the rate limiter state
        """
        return {
            "active_identifiers": len(self._requests),
            "max_entries": self.MAX_ENTRIES,
            "last_cleanup": self._last_cleanup,
            "cleanup_interval": self.CLEANUP_INTERVAL
        }


# Global instances
input_validator = InputValidator()
encryption_service = EncryptionService()
rate_limiter = RateLimiter()
