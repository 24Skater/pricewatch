"""Test service layer functionality."""

import pytest
from unittest.mock import Mock, patch
from app.services.tracker_service import TrackerService
from app.services.profile_service import ProfileService
from app.schemas import TrackerCreate, ProfileCreate
from app.exceptions import ValidationError, DatabaseError


class TestTrackerService:
    """Test TrackerService functionality."""
    
    def test_create_tracker_success(self, db_session, sample_tracker_data):
        """Test successful tracker creation."""
        tracker_data = TrackerCreate(**sample_tracker_data)
        service = TrackerService(db_session)
        
        with patch('app.services.tracker_service.get_price') as mock_get_price:
            mock_get_price.return_value = (99.99, "USD", "Test Product")
            
            tracker = service.create_tracker(tracker_data)
            
            assert tracker.url == sample_tracker_data["url"]
            assert tracker.alert_method == sample_tracker_data["alert_method"]
            assert tracker.contact == sample_tracker_data["contact"]
            assert tracker.last_price == 99.99
    
    def test_create_tracker_invalid_url(self, db_session):
        """Test tracker creation with invalid URL."""
        from pydantic import ValidationError as PydanticValidationError
        
        # Pydantic will validate URL format at schema level
        with pytest.raises(PydanticValidationError):
            tracker_data = TrackerCreate(
                url="invalid-url",
                alert_method="email",
                contact="test@example.com"
            )
    
    def test_create_tracker_invalid_email(self, db_session):
        """Test tracker creation with invalid email."""
        from pydantic import ValidationError as PydanticValidationError
        
        # Pydantic will validate email format at schema level
        with pytest.raises(PydanticValidationError):
            tracker_data = TrackerCreate(
                url="https://example.com",
                alert_method="email",
                contact="invalid-email"
            )
    
    def test_get_tracker(self, db_session, sample_tracker):
        """Test getting a tracker by ID."""
        service = TrackerService(db_session)
        tracker = service.get_tracker(sample_tracker.id)
        
        assert tracker is not None
        assert tracker.id == sample_tracker.id
        assert tracker.url == sample_tracker.url
    
    def test_get_tracker_not_found(self, db_session):
        """Test getting a non-existent tracker."""
        service = TrackerService(db_session)
        tracker = service.get_tracker(999)
        
        assert tracker is None
    
    def test_delete_tracker(self, db_session, sample_tracker):
        """Test deleting a tracker."""
        service = TrackerService(db_session)
        success = service.delete_tracker(sample_tracker.id)
        
        assert success is True
        tracker = service.get_tracker(sample_tracker.id)
        assert tracker is None
    
    def test_delete_tracker_not_found(self, db_session):
        """Test deleting a non-existent tracker."""
        service = TrackerService(db_session)
        success = service.delete_tracker(999)
        
        assert success is False


class TestProfileService:
    """Test ProfileService functionality."""
    
    def test_create_profile_success(self, db_session, sample_profile_data):
        """Test successful profile creation."""
        profile_data = ProfileCreate(**sample_profile_data)
        service = ProfileService(db_session)
        
        profile = service.create_profile(profile_data)
        
        assert profile.name == sample_profile_data["name"]
        assert profile.email_from == sample_profile_data["email_from"]
        assert profile.smtp_host == sample_profile_data["smtp_host"]
    
    def test_create_profile_invalid_email(self, db_session):
        """Test profile creation with invalid email."""
        # email_from is Optional[str] in schema, validation happens in service
        profile_data = ProfileCreate(
            name="Test Profile",
            email_from="invalid-email"
        )
        service = ProfileService(db_session)
        
        # Service validates email and raises DatabaseError wrapping ValidationError
        with pytest.raises(DatabaseError):
            service.create_profile(profile_data)
    
    def test_get_profile(self, db_session, sample_profile):
        """Test getting a profile by ID."""
        service = ProfileService(db_session)
        profile = service.get_profile(sample_profile.id)
        
        assert profile is not None
        assert profile.id == sample_profile.id
        assert profile.name == sample_profile.name
    
    def test_delete_profile(self, db_session, sample_profile):
        """Test deleting a profile."""
        service = ProfileService(db_session)
        success = service.delete_profile(sample_profile.id)
        
        assert success is True
        profile = service.get_profile(sample_profile.id)
        assert profile is None
