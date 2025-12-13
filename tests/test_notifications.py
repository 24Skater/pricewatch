"""Tests for notification sending functionality.

Tests email and SMS notifications with mocked SMTP and Twilio clients.
No actual notifications are sent during testing.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from app.alerts import send_email, send_sms, _smtp_config, _twilio_config
from app.services.notification_service import NotificationService, notification_service


# =============================================================================
# Mock Profile Fixtures
# =============================================================================

@pytest.fixture
def mock_profile():
    """Create a mock notification profile."""
    profile = MagicMock()
    profile.id = 1
    profile.email_from = "custom@example.com"
    profile.smtp_host = "smtp.custom.com"
    profile.smtp_port = 465
    profile.smtp_user = "custom_user"
    profile.smtp_pass = "encrypted_pass"
    profile.twilio_account_sid = "AC_custom_sid"
    profile.twilio_auth_token = "encrypted_token"
    profile.twilio_from_number = "+15551234567"
    return profile


@pytest.fixture
def mock_tracker():
    """Create a mock tracker for notification tests."""
    tracker = MagicMock()
    tracker.id = 1
    tracker.name = "Test Product"
    tracker.url = "https://example.com/product"
    tracker.alert_method = "email"
    tracker.contact = "user@example.com"
    tracker.profile = None
    return tracker


@pytest.fixture
def mock_tracker_sms():
    """Create a mock tracker for SMS notifications."""
    tracker = MagicMock()
    tracker.id = 2
    tracker.name = "SMS Product"
    tracker.url = "https://example.com/sms-product"
    tracker.alert_method = "sms"
    tracker.contact = "+15559876543"
    tracker.profile = None
    return tracker


# =============================================================================
# Test SMTP Configuration
# =============================================================================

class TestSmtpConfig:
    """Tests for SMTP configuration retrieval."""
    
    def test_smtp_config_no_profile(self):
        """Test SMTP config from environment when no profile."""
        config = _smtp_config(None)
        # Should return environment config
        assert "smtp_host" in config
        assert "smtp_port" in config
        assert "email_from" in config
    
    @patch("app.alerts.encryption_service")
    def test_smtp_config_with_profile(self, mock_encryption, mock_profile):
        """Test SMTP config from profile with decryption."""
        mock_encryption.decrypt.return_value = "decrypted_password"
        
        config = _smtp_config(mock_profile)
        
        assert config["email_from"] == "custom@example.com"
        assert config["smtp_host"] == "smtp.custom.com"
        assert config["smtp_port"] == 465
        assert config["smtp_user"] == "custom_user"
        assert config["smtp_pass"] == "decrypted_password"
        mock_encryption.decrypt.assert_called_once_with("encrypted_pass")
    
    @patch("app.alerts.encryption_service")
    def test_smtp_config_decryption_failure(self, mock_encryption, mock_profile):
        """Test SMTP config handles decryption failure gracefully."""
        mock_encryption.decrypt.side_effect = Exception("Decryption failed")
        
        # Should not raise, returns None for password
        config = _smtp_config(mock_profile)
        assert config["smtp_pass"] is None or config["smtp_pass"] == mock_profile.smtp_pass


# =============================================================================
# Test Twilio Configuration
# =============================================================================

class TestTwilioConfig:
    """Tests for Twilio configuration retrieval."""
    
    def test_twilio_config_no_profile(self):
        """Test Twilio config from environment when no profile."""
        config = _twilio_config(None)
        # Should return environment config
        assert "twilio_account_sid" in config
        assert "twilio_auth_token" in config
        assert "twilio_from_number" in config
    
    @patch("app.alerts.encryption_service")
    def test_twilio_config_with_profile(self, mock_encryption, mock_profile):
        """Test Twilio config from profile with decryption."""
        mock_encryption.decrypt.return_value = "decrypted_token"
        
        config = _twilio_config(mock_profile)
        
        assert config["twilio_account_sid"] == "AC_custom_sid"
        assert config["twilio_auth_token"] == "decrypted_token"
        assert config["twilio_from_number"] == "+15551234567"
        mock_encryption.decrypt.assert_called_once_with("encrypted_token")
    
    @patch("app.alerts.encryption_service")
    def test_twilio_config_decryption_failure(self, mock_encryption, mock_profile):
        """Test Twilio config handles decryption failure gracefully."""
        mock_encryption.decrypt.side_effect = Exception("Decryption failed")
        
        # Should not raise
        config = _twilio_config(mock_profile)
        assert "twilio_account_sid" in config


# =============================================================================
# Test send_email()
# =============================================================================

class TestSendEmail:
    """Tests for send_email() function."""
    
    @patch("app.alerts.smtplib.SMTP")
    @patch("app.alerts._smtp_config")
    def test_send_email_success(self, mock_smtp_config, mock_smtp_class):
        """Test successful email sending."""
        # Configure mock SMTP config
        mock_smtp_config.return_value = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "smtp_user": "test_user",
            "smtp_pass": "test_pass",
            "email_from": "from@test.com"
        }
        
        # Configure mock SMTP
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        
        send_email("to@example.com", "Test Subject", "Test Body")
        
        mock_smtp_class.assert_called_once_with("smtp.test.com", 587)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test_user", "test_pass")
        mock_smtp.send_message.assert_called_once()
    
    @patch("app.alerts.settings")
    def test_send_email_skips_when_not_configured(self, mock_settings):
        """Test email is skipped when SMTP not configured."""
        mock_settings.smtp_host = None
        mock_settings.smtp_port = 587
        mock_settings.smtp_user = None
        mock_settings.smtp_pass = None
        mock_settings.from_email = "from@test.com"
        
        # Should not raise, just skip
        send_email("to@example.com", "Test Subject", "Test Body")
        # No assertion needed - just verify no exception
    
    @patch("app.alerts.smtplib.SMTP")
    @patch("app.alerts._smtp_config")
    def test_send_email_raises_on_error(self, mock_smtp_config, mock_smtp_class):
        """Test email raises exception on SMTP error."""
        # Configure mock SMTP config
        mock_smtp_config.return_value = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "smtp_user": "test_user",
            "smtp_pass": "test_pass",
            "email_from": "from@test.com"
        }
        
        mock_smtp_class.side_effect = Exception("SMTP connection failed")
        
        with pytest.raises(Exception):
            send_email("to@example.com", "Test Subject", "Test Body")
    
    @patch("app.alerts.smtplib.SMTP")
    @patch("app.alerts.encryption_service")
    @patch("app.alerts.settings")
    def test_send_email_with_profile(self, mock_settings, mock_encryption, mock_smtp_class, mock_profile):
        """Test email sending with custom profile."""
        mock_settings.from_email = "default@test.com"
        mock_settings.smtp_host = None  # No default
        mock_encryption.decrypt.return_value = "decrypted_pass"
        
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        
        send_email("to@example.com", "Test Subject", "Test Body", profile=mock_profile)
        
        # Should use profile's SMTP settings
        mock_smtp_class.assert_called_once_with("smtp.custom.com", 465)


# =============================================================================
# Test send_sms()
# =============================================================================

class TestSendSms:
    """Tests for send_sms() function."""
    
    @patch("app.alerts.Client")
    @patch("app.alerts._twilio_config")
    def test_send_sms_success(self, mock_twilio_config, mock_client_class):
        """Test successful SMS sending."""
        # Configure mock Twilio config
        mock_twilio_config.return_value = {
            "twilio_account_sid": "AC_test_sid",
            "twilio_auth_token": "test_token",
            "twilio_from_number": "+15551112222"
        }
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        send_sms("+15559998888", "Test SMS Body")
        
        mock_client_class.assert_called_once_with("AC_test_sid", "test_token")
        mock_client.messages.create.assert_called_once_with(
            to="+15559998888",
            from_="+15551112222",
            body="Test SMS Body"
        )
    
    @patch("app.alerts.settings")
    def test_send_sms_skips_when_not_configured(self, mock_settings):
        """Test SMS is skipped when Twilio not configured."""
        mock_settings.twilio_account_sid = None
        mock_settings.twilio_auth_token = None
        mock_settings.twilio_from_number = None
        
        # Should not raise, just skip
        send_sms("+15559998888", "Test SMS Body")
    
    @patch("app.alerts.Client")
    @patch("app.alerts._twilio_config")
    def test_send_sms_raises_on_error(self, mock_twilio_config, mock_client_class):
        """Test SMS raises exception on Twilio error."""
        # Configure mock Twilio config
        mock_twilio_config.return_value = {
            "twilio_account_sid": "AC_test_sid",
            "twilio_auth_token": "test_token",
            "twilio_from_number": "+15551112222"
        }
        
        mock_client_class.side_effect = Exception("Twilio error")
        
        with pytest.raises(Exception):
            send_sms("+15559998888", "Test SMS Body")
    
    @patch("app.alerts.Client")
    @patch("app.alerts.encryption_service")
    @patch("app.alerts.settings")
    def test_send_sms_with_profile(self, mock_settings, mock_encryption, mock_client_class, mock_profile):
        """Test SMS sending with custom profile."""
        mock_settings.twilio_account_sid = None  # No default
        mock_encryption.decrypt.return_value = "decrypted_token"
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        send_sms("+15559998888", "Test SMS Body", profile=mock_profile)
        
        # Should use profile's Twilio settings
        mock_client_class.assert_called_once_with("AC_custom_sid", "decrypted_token")


# =============================================================================
# Test NotificationService
# =============================================================================

class TestNotificationService:
    """Tests for NotificationService class."""
    
    @patch("app.services.notification_service._send_email")
    def test_send_price_alert_email(self, mock_send_email, mock_tracker):
        """Test price alert via email."""
        service = NotificationService()
        
        result = service.send_price_alert(mock_tracker, 99.99, -10.00)
        
        assert result is True
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert call_args[0][0] == "user@example.com"  # to_email
        assert "decreased" in call_args[0][1]  # subject contains direction
        assert "$10.00" in call_args[0][2]  # body contains delta
    
    @patch("app.services.notification_service._send_sms")
    def test_send_price_alert_sms(self, mock_send_sms, mock_tracker_sms):
        """Test price alert via SMS."""
        service = NotificationService()
        
        result = service.send_price_alert(mock_tracker_sms, 49.99, 5.00)
        
        assert result is True
        mock_send_sms.assert_called_once()
        call_args = mock_send_sms.call_args
        assert call_args[0][0] == "+15559876543"  # to_number
        assert "increased" in call_args[0][1]  # body contains direction
    
    @patch("app.services.notification_service._send_email")
    def test_send_price_alert_failure(self, mock_send_email, mock_tracker):
        """Test price alert returns False on failure."""
        mock_send_email.side_effect = Exception("Send failed")
        service = NotificationService()
        
        result = service.send_price_alert(mock_tracker, 99.99, -10.00)
        
        assert result is False
    
    @patch("app.services.notification_service._send_email")
    def test_send_email_delegates(self, mock_send_email):
        """Test NotificationService.send_email delegates to alerts module."""
        service = NotificationService()
        
        service.send_email("test@example.com", "Subject", "Body")
        
        mock_send_email.assert_called_once_with(
            "test@example.com", "Subject", "Body", profile=None
        )
    
    @patch("app.services.notification_service._send_sms")
    def test_send_sms_delegates(self, mock_send_sms):
        """Test NotificationService.send_sms delegates to alerts module."""
        service = NotificationService()
        
        service.send_sms("+15551234567", "Message")
        
        mock_send_sms.assert_called_once_with(
            "+15551234567", "Message", profile=None
        )
    
    def test_singleton_instance_exists(self):
        """Test notification_service singleton is available."""
        assert notification_service is not None
        assert isinstance(notification_service, NotificationService)


# =============================================================================
# Test Credential Decryption Flow
# =============================================================================

class TestCredentialDecryption:
    """Tests for credential decryption in notification flow."""
    
    @patch("app.alerts.smtplib.SMTP")
    @patch("app.alerts.encryption_service")
    @patch("app.alerts.settings")
    def test_email_uses_decrypted_password(self, mock_settings, mock_encryption, mock_smtp_class, mock_profile):
        """Test email sending uses decrypted password from profile."""
        mock_settings.smtp_host = None
        mock_settings.from_email = "default@test.com"
        mock_encryption.decrypt.return_value = "the_real_password"
        
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        
        send_email("to@test.com", "Subject", "Body", profile=mock_profile)
        
        # Verify password was decrypted
        mock_encryption.decrypt.assert_called_with("encrypted_pass")
        # Verify decrypted password was used for login
        mock_smtp.login.assert_called_once_with("custom_user", "the_real_password")
    
    @patch("app.alerts.Client")
    @patch("app.alerts.encryption_service")
    @patch("app.alerts.settings")
    def test_sms_uses_decrypted_token(self, mock_settings, mock_encryption, mock_client_class, mock_profile):
        """Test SMS sending uses decrypted auth token from profile."""
        mock_settings.twilio_account_sid = None
        mock_encryption.decrypt.return_value = "the_real_token"
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        send_sms("+15551234567", "Message", profile=mock_profile)
        
        # Verify token was decrypted
        mock_encryption.decrypt.assert_called_with("encrypted_token")
        # Verify decrypted token was used for client
        mock_client_class.assert_called_once_with("AC_custom_sid", "the_real_token")

