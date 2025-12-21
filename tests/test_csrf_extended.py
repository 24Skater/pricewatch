"""Extended CSRF tests for better coverage."""

import pytest
import time
from unittest.mock import MagicMock, patch
from fastapi import Request
from app.csrf import CSRFTokenManager, csrf_protect, get_csrf_token, validate_csrf_token


class TestCSRFTokenManagerExtended:
    """Extended tests for CSRFTokenManager."""
    
    def test_validate_token_expired(self):
        """Test validation of expired token."""
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        mock_request.session = {}
        
        # Generate token
        token = manager.generate_token(mock_request)
        
        # Manually expire it
        old_time = manager._tokens[token][1]
        manager._tokens[token] = (manager._tokens[token][0], old_time - 4000)  # Expired
        
        # Should fail validation
        result = manager.validate_token(token, mock_request)
        assert result is False
    
    def test_invalidate_token(self):
        """Test token invalidation."""
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        mock_request.session = {}
        
        token = manager.generate_token(mock_request)
        assert token in manager._tokens
        
        manager.invalidate_token(token)
        assert token not in manager._tokens
    
    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens."""
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        mock_request.session = {}
        
        # Generate multiple tokens
        token1 = manager.generate_token(mock_request)
        token2 = manager.generate_token(mock_request)
        
        # Expire one
        old_time = manager._tokens[token1][1]
        manager._tokens[token1] = (manager._tokens[token1][0], old_time - 4000)
        
        # Force cleanup by setting last_cleanup far back
        manager._last_cleanup = time.time() - 400
        
        # Generate another token to trigger cleanup
        token3 = manager.generate_token(mock_request)
        
        # Expired token should be removed
        assert token1 not in manager._tokens
        assert token2 in manager._tokens
        assert token3 in manager._tokens
    
    def test_validate_token_none(self):
        """Test validation with None token."""
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        mock_request.session = {}
        
        result = manager.validate_token(None, mock_request)
        assert result is False
    
    def test_validate_token_not_in_storage(self):
        """Test validation of token not in storage."""
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        mock_request.session = {}
        
        result = manager.validate_token("nonexistent_token", mock_request)
        assert result is False


class TestCSRFProtectFunction:
    """Test csrf_protect function."""
    
    def test_csrf_protect_valid_token(self):
        """Test csrf_protect with valid token."""
        from app.csrf import csrf_manager
        
        mock_request = MagicMock()
        mock_request.session = {}
        mock_request.client.host = "127.0.0.1"
        
        # Generate token using the global manager
        token = csrf_manager.generate_token(mock_request)
        
        result = csrf_protect(mock_request, token)
        assert result is True
    
    def test_csrf_protect_invalid_token(self):
        """Test csrf_protect with invalid token."""
        mock_request = MagicMock()
        mock_request.session = {}
        
        result = csrf_protect(mock_request, "invalid_token")
        assert result is False
    
    def test_csrf_protect_no_token(self):
        """Test csrf_protect with no token."""
        mock_request = MagicMock()
        mock_request.session = {}
        
        result = csrf_protect(mock_request, None)
        assert result is False

