"""CSRF (Cross-Site Request Forgery) protection module.

This module provides CSRF token generation, validation, and middleware
for protecting form submissions against CSRF attacks.
"""

import secrets
import hashlib
import time
import logging
from typing import Optional, Dict, Tuple
from fastapi import Request, HTTPException, status

logger = logging.getLogger("app.csrf")

# CSRF token configuration
CSRF_TOKEN_LENGTH = 32  # Length of the random token
CSRF_TOKEN_EXPIRY = 3600  # Token expiry time in seconds (1 hour)
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_FORM_FIELD = "csrf_token"
CSRF_COOKIE_NAME = "csrf_token"


class CSRFTokenManager:
    """Manages CSRF token generation and validation.
    
    Uses a simple token-based approach where tokens are stored in cookies
    and validated against form submissions or headers.
    """
    
    def __init__(self):
        self._tokens: Dict[str, Tuple[str, float]] = {}  # token -> (secret, timestamp)
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()
    
    def generate_token(self, request: Request) -> str:
        """Generate a new CSRF token for the request.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            str: The generated CSRF token
        """
        # Create a random token
        token = secrets.token_urlsafe(CSRF_TOKEN_LENGTH)
        secret = secrets.token_urlsafe(CSRF_TOKEN_LENGTH)
        
        # Store token with timestamp
        self._tokens[token] = (secret, time.time())
        
        # Periodic cleanup
        self._cleanup_expired_tokens()
        
        return token
    
    def validate_token(self, token: Optional[str], request: Request) -> bool:
        """Validate a CSRF token.
        
        Args:
            token: The token to validate
            request: The FastAPI request object
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        if not token:
            logger.warning(f"CSRF validation failed: no token provided from {request.client.host}")
            return False
        
        # Check if token exists
        if token not in self._tokens:
            logger.warning(f"CSRF validation failed: unknown token from {request.client.host}")
            return False
        
        secret, timestamp = self._tokens[token]
        
        # Check if token has expired
        if time.time() - timestamp > CSRF_TOKEN_EXPIRY:
            logger.warning(f"CSRF validation failed: expired token from {request.client.host}")
            del self._tokens[token]
            return False
        
        return True
    
    def invalidate_token(self, token: str) -> None:
        """Invalidate a CSRF token after use (one-time use tokens).
        
        Args:
            token: The token to invalidate
        """
        if token in self._tokens:
            del self._tokens[token]
    
    def _cleanup_expired_tokens(self) -> None:
        """Remove expired tokens from storage."""
        now = time.time()
        
        # Only cleanup periodically
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = now
        expired = []
        
        for token, (secret, timestamp) in self._tokens.items():
            if now - timestamp > CSRF_TOKEN_EXPIRY:
                expired.append(token)
        
        for token in expired:
            del self._tokens[token]
        
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired CSRF tokens")


# Global CSRF token manager instance
csrf_manager = CSRFTokenManager()


def get_csrf_token(request: Request) -> str:
    """Get or create a CSRF token for the current request.
    
    This function is intended to be used as a Jinja2 template global.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        str: The CSRF token
    """
    # Check if token already exists in request state
    if hasattr(request.state, 'csrf_token'):
        return request.state.csrf_token
    
    # Generate new token
    token = csrf_manager.generate_token(request)
    request.state.csrf_token = token
    
    return token


async def validate_csrf_token(request: Request) -> None:
    """Validate CSRF token from form data or header.
    
    This function should be called in POST/PUT/DELETE endpoints.
    
    Args:
        request: The FastAPI request object
        
    Raises:
        HTTPException: If CSRF validation fails
    """
    # Try to get token from form data first
    token = None
    
    # Check header
    token = request.headers.get(CSRF_HEADER_NAME)
    
    # Check form data if not in header
    if not token:
        try:
            form = await request.form()
            token = form.get(CSRF_FORM_FIELD)
        except Exception:
            pass
    
    # Validate token
    if not csrf_manager.validate_token(token, request):
        logger.warning(
            f"CSRF validation failed for {request.method} {request.url.path} "
            f"from {request.client.host}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed. Please refresh the page and try again."
        )


def csrf_protect(request: Request, token: Optional[str] = None) -> bool:
    """Check if CSRF token is valid (non-raising version).
    
    Args:
        request: The FastAPI request object
        token: Optional token to validate (if not provided, extracted from request)
        
    Returns:
        bool: True if token is valid
    """
    if token is None:
        token = request.headers.get(CSRF_HEADER_NAME)
    
    return csrf_manager.validate_token(token, request)


# List of paths that don't require CSRF protection
CSRF_EXEMPT_PATHS = [
    "/health",
    "/health/detailed",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
]


def is_csrf_exempt(path: str) -> bool:
    """Check if a path is exempt from CSRF protection.
    
    Args:
        path: The request path
        
    Returns:
        bool: True if path is exempt
    """
    return any(path.startswith(exempt) for exempt in CSRF_EXEMPT_PATHS)

