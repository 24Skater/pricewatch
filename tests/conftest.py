"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Tracker, NotificationProfile, PriceHistory


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Create a test client."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


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
