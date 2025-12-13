"""Integration tests for end-to-end flows.

Tests complete user flows from HTTP request through database operations.
All tests use an in-memory SQLite database to avoid affecting production data.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Tracker, NotificationProfile, PriceHistory
from app.services.tracker_service import TrackerService
from app.services.profile_service import ProfileService
from app.services.scheduler_service import SchedulerService
from app.security import rate_limiter


# =============================================================================
# Test Database Setup
# =============================================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Set up fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client with database override."""
    from app.config import settings
    from app.main import verify_csrf
    
    # Override allowed_hosts for testing
    original_hosts = settings.allowed_hosts
    settings.allowed_hosts = ["localhost", "127.0.0.1", "testserver", "*"]
    
    # Override CSRF verification for testing (bypass CSRF in tests)
    async def bypass_csrf():
        return None
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_csrf] = bypass_csrf
    
    # TestClient needs to use a host that's in allowed_hosts
    with TestClient(app, base_url="http://localhost") as test_client:
        yield test_client
    app.dependency_overrides.clear()
    # Restore original hosts
    settings.allowed_hosts = original_hosts


@pytest.fixture
def db_session():
    """Create a database session for direct DB operations."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# Test Tracker Creation Flow
# =============================================================================

class TestTrackerCreationFlow:
    """Test full tracker creation flow: form → database → response."""
    
    @patch("app.services.tracker_service.get_price")
    def test_create_tracker_full_flow(self, mock_get_price, client):
        """Test creating a tracker through the web form."""
        mock_get_price.return_value = (99.99, "USD", "Test Product Title")
        
        # First get the form page to get CSRF token
        response = client.get("/")
        assert response.status_code == 200
        
        # Submit the form (CSRF validation is mocked in test client)
        form_data = {
            "url": "https://example.com/product",
            "alert_method": "email",
            "contact": "test@example.com",
            "selector": ".price",
            "name": "Test Tracker",
            "profile_id": "0",
            "csrf_token": "test_token",
        }
        
        response = client.post("/trackers", data=form_data, follow_redirects=False)
        
        # Should redirect to tracker detail page
        assert response.status_code in [302, 303]
        assert "/tracker/" in response.headers.get("location", "")
    
    @patch("app.services.tracker_service.get_price")
    def test_create_tracker_stores_in_database(self, mock_get_price, db_session):
        """Test that tracker is correctly stored in database."""
        mock_get_price.return_value = (49.99, "USD", "DB Test Product")
        
        from app.schemas import TrackerCreate
        
        tracker_data = TrackerCreate(
            url="https://example.com/db-test",
            alert_method="email",
            contact="db@example.com",
            selector=".db-price",
            name="DB Test Tracker",
            profile_id=None,
        )
        
        service = TrackerService(db_session)
        tracker = service.create_tracker(tracker_data)
        
        # Verify tracker was created
        assert tracker.id is not None
        assert tracker.url == "https://example.com/db-test"
        assert tracker.last_price == 49.99
        
        # Verify it's in the database
        db_tracker = db_session.query(Tracker).filter(Tracker.id == tracker.id).first()
        assert db_tracker is not None
        assert db_tracker.name == "DB Test Tracker"
    
    def test_create_tracker_validation_error(self, client):
        """Test tracker creation with invalid data."""
        form_data = {
            "url": "not-a-valid-url",
            "alert_method": "email",
            "contact": "invalid-email",
            "csrf_token": "test_token",
        }
        
        response = client.post("/trackers", data=form_data, follow_redirects=False)
        
        # Should return error (400 or redirect with error)
        assert response.status_code in [400, 302, 303, 422]


# =============================================================================
# Test Price Refresh Flow
# =============================================================================

class TestPriceRefreshFlow:
    """Test price refresh flow with mocked scraper."""
    
    @patch("app.services.tracker_service.get_price")
    def test_refresh_price_updates_tracker(self, mock_get_price, db_session):
        """Test refreshing price updates tracker and creates history."""
        # Create a tracker
        tracker = Tracker(
            url="https://example.com/refresh-test",
            alert_method="email",
            contact="refresh@example.com",
            last_price=100.00,
        )
        db_session.add(tracker)
        db_session.commit()
        db_session.refresh(tracker)
        
        # Mock new price
        mock_get_price.return_value = (89.99, "USD", "Refresh Test")
        
        service = TrackerService(db_session)
        price, currency = service.refresh_tracker_price(tracker.id)
        
        assert price == 89.99
        assert currency == "USD"
        
        # Verify tracker was updated
        db_session.refresh(tracker)
        assert tracker.last_price == 89.99
        
        # Verify price history was created
        history = db_session.query(PriceHistory).filter(
            PriceHistory.tracker_id == tracker.id
        ).first()
        assert history is not None
        assert history.price == 89.99
        assert history.delta == -10.01  # 89.99 - 100.00
    
    @patch("app.services.tracker_service.get_price")
    @patch("app.services.notification_service.notification_service.send_price_alert")
    def test_refresh_price_sends_notification(self, mock_notify, mock_get_price, db_session):
        """Test that significant price change triggers notification."""
        tracker = Tracker(
            url="https://example.com/notify-test",
            alert_method="email",
            contact="notify@example.com",
            last_price=100.00,
        )
        db_session.add(tracker)
        db_session.commit()
        db_session.refresh(tracker)
        
        # Mock significant price change
        mock_get_price.return_value = (75.00, "USD", "Notify Test")
        mock_notify.return_value = True
        
        service = TrackerService(db_session)
        service.refresh_tracker_price(tracker.id)
        
        # Notification should have been called
        mock_notify.assert_called_once()


# =============================================================================
# Test Profile Creation with Encryption
# =============================================================================

class TestProfileCreationFlow:
    """Test profile creation with encrypted credential storage."""
    
    @patch("app.services.profile_service.encryption_service")
    def test_create_profile_encrypts_credentials(self, mock_encryption, db_session):
        """Test that profile creation encrypts sensitive fields."""
        mock_encryption.encrypt.return_value = "encrypted_value"
        
        from app.schemas import ProfileCreate
        
        profile_data = ProfileCreate(
            name="Encrypted Test Profile",
            email_from="test@example.com",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="smtp_user",
            smtp_pass="secret_password",
            twilio_account_sid="AC123",
            twilio_auth_token="secret_token",
            twilio_from_number="+15551234567",
        )
        
        service = ProfileService(db_session)
        profile = service.create_profile(profile_data)
        
        # Verify encryption was called for sensitive fields
        assert mock_encryption.encrypt.call_count == 2  # smtp_pass and twilio_auth_token
        
        # Verify profile was created
        assert profile.id is not None
        assert profile.name == "Encrypted Test Profile"
    
    def test_create_profile_via_api(self, client):
        """Test profile creation through web form."""
        form_data = {
            "name": "API Test Profile",
            "email_from": "api@example.com",
            "smtp_host": "smtp.api.com",
            "smtp_port": "587",
            "smtp_user": "api_user",
            "smtp_pass": "api_pass",
            "twilio_account_sid": "",
            "twilio_auth_token": "",
            "twilio_from_number": "",
            "csrf_token": "test_token",
        }
        
        response = client.post("/admin/profiles/new", data=form_data, follow_redirects=False)
        
        # Should redirect to profiles list
        assert response.status_code in [302, 303]
        assert "/admin/profiles" in response.headers.get("location", "")


# =============================================================================
# Test Scheduler Polling
# =============================================================================

class TestSchedulerPolling:
    """Test scheduler polling with mocked scraper."""
    
    @patch("app.services.scheduler_service.get_price")
    def test_poll_all_trackers(self, mock_get_price, db_session):
        """Test polling all active trackers."""
        # Create active trackers
        tracker1 = Tracker(
            url="https://example.com/poll1",
            alert_method="email",
            contact="poll1@example.com",
            is_active=True,
            last_price=50.00,
        )
        tracker2 = Tracker(
            url="https://example.com/poll2",
            alert_method="sms",
            contact="+15551234567",
            is_active=True,
            last_price=75.00,
        )
        # Inactive tracker should not be polled
        tracker3 = Tracker(
            url="https://example.com/inactive",
            alert_method="email",
            contact="inactive@example.com",
            is_active=False,
        )
        db_session.add_all([tracker1, tracker2, tracker3])
        db_session.commit()
        
        # Mock price responses
        mock_get_price.return_value = (49.99, "USD", "Polled")
        
        service = SchedulerService(db_session)
        service.poll_all_trackers()
        
        # Should only poll active trackers (2 calls)
        assert mock_get_price.call_count == 2
    
    @patch("app.services.scheduler_service.get_price")
    def test_poll_continues_on_error(self, mock_get_price, db_session):
        """Test polling continues even if one tracker fails."""
        tracker1 = Tracker(
            url="https://example.com/fail",
            alert_method="email",
            contact="fail@example.com",
            is_active=True,
        )
        tracker2 = Tracker(
            url="https://example.com/success",
            alert_method="email",
            contact="success@example.com",
            is_active=True,
        )
        db_session.add_all([tracker1, tracker2])
        db_session.commit()
        
        # First call fails, second succeeds
        mock_get_price.side_effect = [
            Exception("Scraping failed"),
            (99.99, "USD", "Success"),
        ]
        
        service = SchedulerService(db_session)
        # Should not raise exception
        service.poll_all_trackers()
        
        # Both should have been attempted
        assert mock_get_price.call_count == 2


# =============================================================================
# Test Rate Limiting
# =============================================================================

class TestRateLimiting:
    """Test rate limiting behavior."""
    
    def test_rate_limiter_allows_within_limit(self):
        """Test requests within limit are allowed."""
        # Clear any existing state
        rate_limiter._requests = {}
        
        identifier = "test_ip_allow"
        limit = 5
        
        for i in range(limit):
            result = rate_limiter.is_allowed(identifier, limit)
            assert result is True, f"Request {i+1} should be allowed"
    
    def test_rate_limiter_blocks_over_limit(self):
        """Test requests over limit are blocked."""
        rate_limiter._requests = {}
        
        identifier = "test_ip_block"
        limit = 3
        
        # Use up the limit
        for i in range(limit):
            rate_limiter.is_allowed(identifier, limit)
        
        # Next request should be blocked
        result = rate_limiter.is_allowed(identifier, limit)
        assert result is False
    
    def test_rate_limiter_different_identifiers(self):
        """Test rate limiter tracks identifiers separately."""
        rate_limiter._requests = {}
        
        limit = 2
        
        # Fill up one identifier
        for _ in range(limit):
            rate_limiter.is_allowed("ip1", limit)
        
        # Different identifier should still be allowed
        result = rate_limiter.is_allowed("ip2", limit)
        assert result is True


# =============================================================================
# Test Health Endpoints
# =============================================================================

class TestHealthEndpoints:
    """Test health check endpoints return correct responses."""
    
    def test_health_endpoint(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data
    
    def test_detailed_health_endpoint(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "checks" in data
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        # Should return some metric data
        assert isinstance(data, dict)

