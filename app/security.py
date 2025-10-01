import os
import re
import secrets
import hashlib
from typing import Optional
from urllib.parse import urlparse
from cryptography.fernet import Fernet
from app.config import settings


class SecurityError(Exception):
    """Security-related exception."""
    pass


class InputValidator:
    """Input validation utilities."""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and security."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Check for dangerous schemes
            if parsed.scheme not in ['http', 'https']:
                return False
                
            # Check for localhost/private IPs in production
            if settings.environment == "production":
                if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
                    return False
                    
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate phone number format."""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        return len(digits) >= 10 and len(digits) <= 15
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        if not text:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', text)
        
        # Limit length
        return sanitized[:max_length].strip()


class EncryptionService:
    """Service for encrypting/decrypting sensitive data."""
    
    def __init__(self):
        self._key = self._get_or_create_key()
        self._cipher = Fernet(self._key)
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        key_file = "encryption.key"
        
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not data:
            return ""
        return self._cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not encrypted_data:
            return ""
        return self._cipher.decrypt(encrypted_data.encode()).decode()


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self._requests = {}
    
    def is_allowed(self, identifier: str, limit: int, window: int = 60) -> bool:
        """Check if request is allowed based on rate limit."""
        import time
        now = time.time()
        
        if identifier not in self._requests:
            self._requests[identifier] = []
        
        # Clean old requests
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


# Global instances
input_validator = InputValidator()
encryption_service = EncryptionService()
rate_limiter = RateLimiter()
