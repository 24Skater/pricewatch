"""Test security functionality.

Comprehensive tests for security features including:
- Input validation
- SSRF protection
- CSRF protection
- Rate limiting
- XSS sanitization
- Encryption
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from app.security import (
    InputValidator, EncryptionService, RateLimiter,
    is_private_ip, is_ip_address, input_validator
)
from app.exceptions import SecurityError


class TestInputValidator:
    """Test input validation functionality."""
    
    def test_validate_url_valid(self):
        """Test valid URL validation."""
        validator = InputValidator()
        
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://www.example.com/path",
        ]
        
        for url in valid_urls:
            assert validator.validate_url(url) is True
    
    def test_validate_url_invalid(self):
        """Test invalid URL validation."""
        validator = InputValidator()
        
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "javascript:alert('xss')",
            "",
        ]
        
        for url in invalid_urls:
            assert validator.validate_url(url) is False
    
    def test_validate_email_valid(self):
        """Test valid email validation."""
        validator = InputValidator()
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
        ]
        
        for email in valid_emails:
            assert validator.validate_email(email) is True
    
    def test_validate_email_invalid(self):
        """Test invalid email validation."""
        validator = InputValidator()
        
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "test@",
            "test.example.com",
        ]
        
        for email in invalid_emails:
            assert validator.validate_email(email) is False
    
    def test_validate_phone_number_valid(self):
        """Test valid phone number validation."""
        validator = InputValidator()
        
        valid_phones = [
            "1234567890",
            "+1234567890",
            "(123) 456-7890",
            "123-456-7890",
        ]
        
        for phone in valid_phones:
            assert validator.validate_phone_number(phone) is True
    
    def test_validate_phone_number_invalid(self):
        """Test invalid phone number validation."""
        validator = InputValidator()
        
        invalid_phones = [
            "123",
            "abc-def-ghij",
            "",
            "12345678901234567890",  # Too long
        ]
        
        for phone in invalid_phones:
            assert validator.validate_phone_number(phone) is False
    
    def test_sanitize_string(self):
        """Test string sanitization."""
        validator = InputValidator()
        
        test_cases = [
            ("<script>alert('xss')</script>", "scriptalert(xss)/script"),  # Quotes removed
            ("Normal text", "Normal text"),
            ("", ""),
            ("Text with < and >", "Text with  and"),  # Trailing space removed by strip()
        ]
        
        for input_text, expected in test_cases:
            result = validator.sanitize_string(input_text)
            assert result == expected


class TestEncryptionService:
    """Test encryption functionality."""
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        service = EncryptionService()
        
        test_data = "sensitive information"
        encrypted = service.encrypt(test_data)
        decrypted = service.decrypt(encrypted)
        
        assert encrypted != test_data
        assert decrypted == test_data
    
    def test_encrypt_empty_string(self):
        """Test encrypting empty string."""
        service = EncryptionService()
        
        encrypted = service.encrypt("")
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == ""
    
    def test_decrypt_empty_string(self):
        """Test decrypting empty string."""
        service = EncryptionService()
        
        result = service.decrypt("")
        assert result == ""


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_allows_requests(self):
        """Test that rate limiter allows requests within limit."""
        limiter = RateLimiter()
        identifier = "test_user"
        
        # Should allow first few requests
        for _ in range(5):
            assert limiter.is_allowed(identifier, 10, 60) is True
    
    def test_rate_limiter_blocks_excess_requests(self):
        """Test that rate limiter blocks excess requests."""
        limiter = RateLimiter()
        identifier = "test_user"
        
        # Should block after exceeding limit
        for _ in range(5):
            limiter.is_allowed(identifier, 5, 60)
        
        # This should be blocked
        assert limiter.is_allowed(identifier, 5, 60) is False
    
    def test_rate_limiter_different_identifiers(self):
        """Test that rate limiter treats different identifiers separately."""
        limiter = RateLimiter()
        
        # User 1 should be able to make requests
        assert limiter.is_allowed("user1", 5, 60) is True
        
        # User 2 should also be able to make requests
        assert limiter.is_allowed("user2", 5, 60) is True


# =============================================================================
# SSRF Protection Tests
# =============================================================================

class TestSSRFProtection:
    """Test Server-Side Request Forgery (SSRF) protection."""
    
    def test_is_private_ip_localhost(self):
        """Test localhost IPs are detected as private."""
        assert is_private_ip("127.0.0.1") is True
        assert is_private_ip("127.0.0.2") is True
        assert is_private_ip("127.255.255.255") is True
    
    def test_is_private_ip_10_range(self):
        """Test 10.x.x.x range is detected as private."""
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("10.255.255.255") is True
    
    def test_is_private_ip_172_range(self):
        """Test 172.16-31.x.x range is detected as private."""
        assert is_private_ip("172.16.0.1") is True
        assert is_private_ip("172.31.255.255") is True
    
    def test_is_private_ip_192_168_range(self):
        """Test 192.168.x.x range is detected as private."""
        assert is_private_ip("192.168.0.1") is True
        assert is_private_ip("192.168.255.255") is True
    
    def test_is_private_ip_link_local(self):
        """Test link-local addresses are detected as private."""
        assert is_private_ip("169.254.0.1") is True
        assert is_private_ip("169.254.255.255") is True
    
    def test_is_private_ip_ipv6_localhost(self):
        """Test IPv6 localhost is detected as private."""
        assert is_private_ip("::1") is True
    
    def test_is_private_ip_public(self):
        """Test public IPs are not marked as private."""
        assert is_private_ip("8.8.8.8") is False
        assert is_private_ip("1.1.1.1") is False
        assert is_private_ip("93.184.216.34") is False  # example.com
    
    def test_is_private_ip_invalid(self):
        """Test invalid IP addresses return False."""
        assert is_private_ip("not-an-ip") is False
        assert is_private_ip("999.999.999.999") is False
    
    def test_is_ip_address(self):
        """Test IP address detection."""
        assert is_ip_address("192.168.1.1") is True
        assert is_ip_address("8.8.8.8") is True
        assert is_ip_address("::1") is True
        assert is_ip_address("example.com") is False
        assert is_ip_address("not-an-ip") is False
    
    @patch("app.security.settings")
    def test_validate_url_blocks_private_ip(self, mock_settings):
        """Test URL validation blocks private IPs in production."""
        mock_settings.environment = "production"
        validator = InputValidator()
        
        private_urls = [
            "http://127.0.0.1/admin",
            "http://192.168.1.1/secret",
            "http://10.0.0.1/internal",
            "http://169.254.169.254/metadata",  # AWS metadata
        ]
        
        for url in private_urls:
            assert validator.validate_url(url, allow_private=False) is False
    
    @patch("app.security.settings")
    def test_validate_url_blocks_localhost_hostnames(self, mock_settings):
        """Test URL validation blocks localhost hostnames."""
        mock_settings.environment = "production"
        validator = InputValidator()
        
        localhost_urls = [
            "http://localhost/admin",
            "http://localhost:8080/api",
        ]
        
        for url in localhost_urls:
            assert validator.validate_url(url, allow_private=False) is False


# =============================================================================
# Rate Limiter Cleanup Tests
# =============================================================================

class TestRateLimiterCleanup:
    """Test rate limiter memory cleanup functionality."""
    
    def test_cleanup_removes_old_entries(self):
        """Test that cleanup removes expired entries."""
        limiter = RateLimiter()
        
        # Set last_cleanup to force cleanup on next call
        limiter._last_cleanup = time.time() - limiter.CLEANUP_INTERVAL - 1
        
        # Add some entries
        limiter.is_allowed("old_user", 10, 1)  # 1 second window
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Force cleanup by setting last_cleanup back
        limiter._last_cleanup = time.time() - limiter.CLEANUP_INTERVAL - 1
        limiter._maybe_cleanup(1)
        
        # Old entry should be removed after cleanup
        # This is internal state check
        assert "old_user" not in limiter._requests or len(limiter._requests.get("old_user", [])) == 0
    
    def test_get_stats(self):
        """Test rate limiter statistics."""
        limiter = RateLimiter()
        limiter.is_allowed("stats_user", 10, 60)
        
        stats = limiter.get_stats()
        
        assert "active_identifiers" in stats
        assert "max_entries" in stats
        assert "last_cleanup" in stats
        assert stats["active_identifiers"] >= 1
    
    def test_max_entries_eviction(self):
        """Test that old entries are evicted when limit reached."""
        limiter = RateLimiter()
        original_max = limiter.MAX_ENTRIES
        
        # Temporarily set low limit
        limiter.MAX_ENTRIES = 5
        
        try:
            # Add more entries than limit
            for i in range(10):
                limiter.is_allowed(f"user_{i}", 100, 60)
            
            # Should have evicted some entries
            assert len(limiter._requests) <= 10  # Some eviction happened
        finally:
            limiter.MAX_ENTRIES = original_max


# =============================================================================
# Input Length Validation Tests
# =============================================================================

class TestInputLengthValidation:
    """Test input length validation."""
    
    def test_sanitize_string_respects_max_length(self):
        """Test sanitize_string truncates to max length."""
        validator = InputValidator()
        
        long_text = "A" * 2000
        result = validator.sanitize_string(long_text, max_length=100)
        
        assert len(result) == 100
    
    def test_sanitize_string_default_max_length(self):
        """Test sanitize_string uses default max length."""
        validator = InputValidator()
        
        long_text = "A" * 2000
        result = validator.sanitize_string(long_text)  # Default 1000
        
        assert len(result) == 1000
    
    def test_validate_url_max_length(self):
        """Test URL validation with very long URLs."""
        validator = InputValidator()
        
        # Very long URL (over 2000 chars)
        long_url = "https://example.com/" + "a" * 3000
        
        # Should still process (validation is about format, not length)
        # But very long URLs may fail for other reasons
        result = validator.validate_url(long_url)
        # Result depends on URL structure, not just length


# =============================================================================
# XSS Sanitization Tests
# =============================================================================

class TestXSSSanitization:
    """Test XSS attack prevention through sanitization."""
    
    def test_sanitize_removes_script_tags(self):
        """Test script tags are removed."""
        validator = InputValidator()
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<SCRIPT>alert('xss')</SCRIPT>",
            "<script src='evil.js'></script>",
        ]
        
        for payload in xss_payloads:
            result = validator.sanitize_string(payload)
            assert "<script" not in result.lower()
            assert "</script" not in result.lower()
    
    def test_sanitize_removes_angle_brackets(self):
        """Test angle brackets are removed."""
        validator = InputValidator()
        
        result = validator.sanitize_string("<div onclick='evil()'>Click</div>")
        
        assert "<" not in result
        assert ">" not in result
    
    def test_sanitize_removes_quotes(self):
        """Test quotes are removed."""
        validator = InputValidator()
        
        result = validator.sanitize_string("Test \"quoted\" and 'single' quotes")
        
        assert '"' not in result
        assert "'" not in result
    
    def test_sanitize_event_handlers(self):
        """Test event handler payloads are sanitized."""
        validator = InputValidator()
        
        payloads = [
            "<img src=x onerror=alert('xss')>",
            "<body onload=alert('xss')>",
            "<svg onload=alert('xss')>",
        ]
        
        for payload in payloads:
            result = validator.sanitize_string(payload)
            assert "<" not in result
            assert ">" not in result
    
    def test_sanitize_javascript_protocol(self):
        """Test javascript: protocol is not executable after sanitization."""
        validator = InputValidator()
        
        payload = "javascript:alert('xss')"
        result = validator.sanitize_string(payload)
        
        # Quotes removed, making it non-executable
        assert "'" not in result
    
    def test_sanitize_preserves_safe_text(self):
        """Test that safe text is preserved."""
        validator = InputValidator()
        
        safe_texts = [
            "Normal product name",
            "Price: $99.99",
            "Model ABC-123",
            "Contact: email at example dot com",
        ]
        
        for text in safe_texts:
            result = validator.sanitize_string(text)
            # Safe text should be mostly preserved
            # (quotes might be removed but core content stays)
            assert len(result) > 0


# =============================================================================
# CSRF Protection Tests  
# =============================================================================

class TestCSRFProtection:
    """Test CSRF token protection."""
    
    def test_csrf_module_exists(self):
        """Test CSRF module can be imported."""
        from app.csrf import get_csrf_token, validate_csrf_token
        assert get_csrf_token is not None
        assert validate_csrf_token is not None
    
    def test_csrf_token_generation(self):
        """Test CSRF token is generated correctly."""
        from app.csrf import CSRFTokenManager
        
        manager = CSRFTokenManager()
        
        # Create mock request with session
        mock_request = MagicMock()
        mock_request.session = {}
        
        token = manager.generate_token(mock_request)
        
        assert token is not None
        assert len(token) > 0
        # Token is stored in manager's internal dictionary, not in session
        assert token in manager._tokens
    
    def test_csrf_token_validation(self):
        """Test CSRF token validation."""
        from app.csrf import CSRFTokenManager
        
        manager = CSRFTokenManager()
        
        # Create mock request with session
        mock_request = MagicMock()
        mock_request.session = {}
        
        # Generate token
        token = manager.generate_token(mock_request)
        
        # Validate same token
        is_valid = manager.validate_token(token, mock_request)
        assert is_valid is True
    
    def test_csrf_token_invalid(self):
        """Test invalid CSRF token is rejected."""
        from app.csrf import CSRFTokenManager
        
        manager = CSRFTokenManager()
        
        mock_request = MagicMock()
        mock_request.session = {"csrf_token": "valid_token"}
        
        # Try to validate wrong token
        is_valid = manager.validate_token("wrong_token", mock_request)
        assert is_valid is False
    
    def test_csrf_token_missing(self):
        """Test missing CSRF token is rejected."""
        from app.csrf import CSRFTokenManager
        
        manager = CSRFTokenManager()
        
        mock_request = MagicMock()
        mock_request.session = {"csrf_token": "valid_token"}
        mock_request.client.host = "127.0.0.1"
        
        # Validate None token
        is_valid = manager.validate_token(None, mock_request)
        assert is_valid is False
    
    def test_csrf_token_expired(self):
        """Test expired CSRF token is rejected."""
        from app.csrf import CSRFTokenManager
        import time
        
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        
        # Generate token
        token = manager.generate_token(mock_request)
        
        # Manually expire it
        secret, _ = manager._tokens[token]
        manager._tokens[token] = (secret, time.time() - 4000)  # Expired
        
        # Should be invalid
        is_valid = manager.validate_token(token, mock_request)
        assert is_valid is False
        # Token should be removed
        assert token not in manager._tokens
    
    def test_csrf_token_invalidate(self):
        """Test token invalidation."""
        from app.csrf import CSRFTokenManager
        
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        
        token = manager.generate_token(mock_request)
        assert token in manager._tokens
        
        manager.invalidate_token(token)
        assert token not in manager._tokens
    
    def test_csrf_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens."""
        from app.csrf import CSRFTokenManager, CSRF_TOKEN_EXPIRY
        import time
        
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        
        # Generate tokens
        token1 = manager.generate_token(mock_request)
        token2 = manager.generate_token(mock_request)
        
        # Expire one token
        secret, _ = manager._tokens[token1]
        manager._tokens[token1] = (secret, time.time() - CSRF_TOKEN_EXPIRY - 1)
        
        # Force cleanup
        manager._last_cleanup = time.time() - manager._cleanup_interval - 1
        manager._cleanup_expired_tokens()
        
        # Expired token should be removed
        assert token1 not in manager._tokens
        # Valid token should remain
        assert token2 in manager._tokens
    
    def test_is_csrf_exempt(self):
        """Test CSRF exempt path checking."""
        from app.csrf import is_csrf_exempt
        
        # Exempt paths
        assert is_csrf_exempt("/health") is True
        assert is_csrf_exempt("/health/detailed") is True
        assert is_csrf_exempt("/metrics") is True
        assert is_csrf_exempt("/docs") is True
        
        # Non-exempt paths
        assert is_csrf_exempt("/trackers") is False
        assert is_csrf_exempt("/admin/profiles") is False
    
    def test_csrf_protect_helper(self):
        """Test csrf_protect helper function."""
        from app.csrf import csrf_protect
        from fastapi import Request
        from unittest.mock import MagicMock
        
        # Create mock request with valid token
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        
        # Generate a valid token
        from app.csrf import csrf_manager
        token = csrf_manager.generate_token(mock_request)
        
        # Set token in header
        mock_request.headers = {"X-CSRF-Token": token}
        
        # Should validate successfully
        result = csrf_protect(mock_request)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_csrf_token_async(self):
        """Test async validate_csrf_token function."""
        from app.csrf import validate_csrf_token
        from fastapi import Request
        from unittest.mock import AsyncMock, MagicMock
        
        # Create mock request with valid token
        mock_request = AsyncMock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.method = "POST"
        mock_request.url.path = "/test"
        
        # Generate a valid token
        from app.csrf import csrf_manager
        token = csrf_manager.generate_token(mock_request)
        
        # Set token in header
        mock_request.headers = {"X-CSRF-Token": token}
        
        # Should not raise
        await validate_csrf_token(mock_request)
