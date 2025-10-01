"""Test security functionality."""

import pytest
from app.security import InputValidator, EncryptionService, RateLimiter
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
            ("<script>alert('xss')</script>", "scriptalert('xss')/script"),
            ("Normal text", "Normal text"),
            ("", ""),
            ("Text with < and >", "Text with  and "),
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
