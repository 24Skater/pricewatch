"""Test configuration and fixtures.

Provides reusable fixtures for testing the Pricewatch application.
All database fixtures use an in-memory SQLite database.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Tracker, NotificationProfile, PriceHistory
from app.security import encryption_service


# =============================================================================
# Database Configuration
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


# =============================================================================
# Core Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test.
    
    Creates all tables before the test and drops them after.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Create a test client with database override.
    
    The test client can be used to make HTTP requests to the application.
    """
    from app.config import settings
    from app.main import verify_csrf
    
    # Override allowed_hosts for testing
    original_hosts = settings.allowed_hosts
    settings.allowed_hosts = ["localhost", "127.0.0.1", "testserver", "*"]
    
    # Override CSRF verification for testing (bypass CSRF in tests)
    async def bypass_csrf():
        return None
    
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_csrf] = bypass_csrf
    # TestClient needs to use a host that's in allowed_hosts
    with TestClient(app, base_url="http://localhost") as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    # Restore original hosts
    settings.allowed_hosts = original_hosts


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_tracker_data():
    """Sample tracker data for testing."""
    return {
        "url": "https://example.com/product",
        "alert_method": "email",
        "contact": "test@example.com",
        "selector": ".price",
        "name": "Test Product",
    }


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing."""
    return {
        "name": "Test Profile",
        "email_from": "alerts@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "test@example.com",
        "smtp_pass": "testpass",
    }


@pytest.fixture
def sample_tracker(db_session, sample_tracker_data):
    """Create a sample tracker in the database."""
    tracker = Tracker(**sample_tracker_data)
    db_session.add(tracker)
    db_session.commit()
    db_session.refresh(tracker)
    return tracker


@pytest.fixture
def sample_profile(db_session, sample_profile_data):
    """Create a sample profile in the database."""
    profile = NotificationProfile(**sample_profile_data)
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


# =============================================================================
# Tracker with Price History Fixture
# =============================================================================

@pytest.fixture
def tracker_with_history(db_session):
    """Create a tracker with price history for testing price trends.
    
    Creates a tracker with 5 price history entries over the past 5 days.
    """
    tracker = Tracker(
        url="https://example.com/price-history-product",
        alert_method="email",
        contact="history@example.com",
        name="Price History Product",
        last_price=89.99,
        currency="USD",
        is_active=True,
    )
    db_session.add(tracker)
    db_session.commit()
    db_session.refresh(tracker)
    
    # Create price history entries
    prices = [99.99, 94.99, 92.99, 89.99, 89.99]
    now = datetime.now(timezone.utc)
    
    for i, price in enumerate(prices):
        delta = prices[i-1] - price if i > 0 else None
        history = PriceHistory(
            tracker_id=tracker.id,
            price=price,
            delta=delta,
            checked_at=now - timedelta(days=len(prices) - i - 1),
        )
        db_session.add(history)
    
    db_session.commit()
    return tracker


# =============================================================================
# Profile with Encrypted Credentials Fixture
# =============================================================================

@pytest.fixture
def profile_with_encrypted_credentials(db_session):
    """Create a profile with encrypted SMTP and Twilio credentials.
    
    Uses the actual encryption service to encrypt credentials.
    """
    profile = NotificationProfile(
        name="Encrypted Profile",
        email_from="encrypted@example.com",
        smtp_host="smtp.encrypted.com",
        smtp_port=587,
        smtp_user="encrypted_user",
        smtp_pass=encryption_service.encrypt("super_secret_password"),
        twilio_account_sid="AC123456789",
        twilio_auth_token=encryption_service.encrypt("twilio_secret_token"),
        twilio_from_number="+15551234567",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


# =============================================================================
# Mock Scraper Fixtures
# =============================================================================

@pytest.fixture
def mock_scraper_success():
    """Mock scraper that returns successful price extraction.
    
    Returns a price of $99.99 with USD currency.
    """
    with patch("app.scraper.fetch_html") as mock_fetch:
        mock_fetch.return_value = """
        <!DOCTYPE html>
        <html>
        <head><title>Mock Product</title></head>
        <body>
            <script type="application/ld+json">
            {"@type": "Product", "offers": {"price": "99.99", "priceCurrency": "USD"}}
            </script>
        </body>
        </html>
        """
        yield mock_fetch


@pytest.fixture
def mock_scraper_failure():
    """Mock scraper that fails to extract price.
    
    Returns HTML with no price information.
    """
    with patch("app.scraper.fetch_html") as mock_fetch:
        mock_fetch.return_value = """
        <!DOCTYPE html>
        <html>
        <head><title>No Price Page</title></head>
        <body><div>No price here</div></body>
        </html>
        """
        yield mock_fetch


@pytest.fixture
def mock_scraper_network_error():
    """Mock scraper that raises a network error."""
    with patch("app.scraper.fetch_html") as mock_fetch:
        import requests
        mock_fetch.side_effect = requests.RequestException("Network error")
        yield mock_fetch


@pytest.fixture
def mock_get_price():
    """Mock the get_price function directly.
    
    Returns (price, currency, title) tuple.
    """
    with patch("app.scraper.get_price") as mock:
        mock.return_value = (99.99, "USD", "Mocked Product")
        yield mock


# =============================================================================
# Mock SMTP Server Fixture
# =============================================================================

@pytest.fixture
def mock_smtp_server():
    """Mock SMTP server for testing email sending.
    
    Captures all sent emails for assertion.
    """
    sent_emails = []
    
    class MockSMTP:
        def __init__(self, host, port):
            self.host = host
            self.port = port
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
        
        def starttls(self):
            pass
        
        def login(self, user, password):
            pass
        
        def send_message(self, msg):
            sent_emails.append({
                "to": msg["To"],
                "from": msg["From"],
                "subject": msg["Subject"],
                "body": msg.get_payload(),
            })
    
    with patch("app.alerts.smtplib.SMTP", MockSMTP):
        yield sent_emails


# =============================================================================
# Mock Twilio Client Fixture
# =============================================================================

@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client for testing SMS sending.
    
    Captures all sent SMS messages for assertion.
    """
    sent_sms = []
    
    class MockTwilioClient:
        def __init__(self, account_sid, auth_token):
            self.account_sid = account_sid
            self.auth_token = auth_token
            self.messages = self
        
        def create(self, to, from_, body):
            sent_sms.append({
                "to": to,
                "from": from_,
                "body": body,
            })
            return MagicMock(sid="SM123456")
    
    with patch("app.alerts.Client", MockTwilioClient):
        yield sent_sms


# =============================================================================
# Authentication Fixture (Future Use)
# =============================================================================

@pytest.fixture
def authenticated_session():
    """Create an authenticated session for protected endpoints.
    
    This fixture is a placeholder for future authentication implementation.
    Currently returns a mock session object.
    """
    session = MagicMock()
    session.user_id = 1
    session.username = "test_user"
    session.is_authenticated = True
    session.csrf_token = "test_csrf_token_12345"
    return session


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state between tests."""
    from app.security import rate_limiter
    original_requests = rate_limiter._requests.copy()
    yield
    rate_limiter._requests = original_requests


@pytest.fixture
def clean_database(db_session):
    """Ensure database is clean before test.
    
    Explicitly deletes all records from all tables.
    """
    db_session.query(PriceHistory).delete()
    db_session.query(Tracker).delete()
    db_session.query(NotificationProfile).delete()
    db_session.commit()
    yield db_session
