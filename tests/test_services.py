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
    
    def test_update_tracker(self, db_session, sample_tracker):
        """Test updating a tracker."""
        service = TrackerService(db_session)
        
        updated_data = TrackerCreate(
            url="https://example.com/updated",
            alert_method="sms",
            contact="+15551234567",
            name="Updated Tracker"
        )
        
        updated = service.update_tracker(sample_tracker.id, updated_data)
        
        assert updated is not None
        assert updated.url == "https://example.com/updated"
        assert updated.alert_method == "sms"
        assert updated.name == "Updated Tracker"
    
    def test_update_tracker_with_profile(self, db_session, sample_tracker, sample_profile):
        """Test updating tracker with profile."""
        service = TrackerService(db_session)
        
        updated_data = TrackerCreate(
            url="https://example.com/updated",
            alert_method="email",
            contact="test@example.com",
            profile_id=sample_profile.id
        )
        
        updated = service.update_tracker(sample_tracker.id, updated_data)
        
        assert updated is not None
        assert updated.profile_id == sample_profile.id
    
    def test_update_tracker_invalid_phone(self, db_session, sample_tracker):
        """Test updating tracker with invalid phone number."""
        service = TrackerService(db_session)
        
        updated_data = TrackerCreate(
            url="https://example.com/updated",
            alert_method="sms",
            contact="123",  # Invalid phone (too short)
            name="Updated Tracker"
        )
        
        # Should raise ValidationError from service layer
        with pytest.raises((ValidationError, DatabaseError)):
            service.update_tracker(sample_tracker.id, updated_data)
    
    def test_update_tracker_not_found(self, db_session):
        """Test updating non-existent tracker."""
        service = TrackerService(db_session)
        
        updated_data = TrackerCreate(
            url="https://example.com",
            alert_method="email",
            contact="test@example.com"
        )
        result = service.update_tracker(999, updated_data)
        
        assert result is None
    
    def test_refresh_tracker_price(self, db_session, sample_tracker):
        """Test refreshing tracker price."""
        service = TrackerService(db_session)
        
        with patch('app.services.tracker_service.get_price') as mock_get_price:
            mock_get_price.return_value = (89.99, "USD", "Updated Product")
            
            price, currency = service.refresh_tracker_price(sample_tracker.id)
            
            assert price == 89.99
            assert currency == "USD"
            
            # Verify tracker was updated
            updated = service.get_tracker(sample_tracker.id)
            assert updated.last_price == 89.99
    
    def test_refresh_tracker_price_not_found(self, db_session):
        """Test refreshing price for non-existent tracker."""
        service = TrackerService(db_session)
        
        with pytest.raises(ValidationError):
            service.refresh_tracker_price(999)
    
    def test_get_all_trackers_pagination(self, db_session):
        """Test get_all_trackers with pagination."""
        from app.models import Tracker
        
        service = TrackerService(db_session)
        
        # Create multiple trackers
        for i in range(5):
            tracker = Tracker(
                url=f"https://example.com/product{i}",
                alert_method="email",
                contact=f"test{i}@example.com"
            )
            db_session.add(tracker)
        db_session.commit()
        
        # Get first page
        trackers, total = service.get_all_trackers(page=1, per_page=2)
        
        assert len(trackers) == 2
        assert total == 5
        
        # Get second page
        trackers2, total2 = service.get_all_trackers(page=2, per_page=2)
        
        assert len(trackers2) == 2
        assert total2 == 5
        assert trackers[0].id != trackers2[0].id


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
    
    def test_get_all_profiles(self, db_session, sample_profile):
        """Test getting all profiles."""
        service = ProfileService(db_session)
        profiles = service.get_all_profiles()
        
        assert len(profiles) >= 1
        assert any(p.id == sample_profile.id for p in profiles)
    
    def test_update_profile(self, db_session, sample_profile):
        """Test updating a profile."""
        service = ProfileService(db_session)
        
        updated_data = ProfileCreate(
            name="Updated Profile",
            email_from="updated@example.com",
            smtp_host="smtp.updated.com",
            smtp_port=465
        )
        
        updated = service.update_profile(sample_profile.id, updated_data)
        
        assert updated is not None
        assert updated.name == "Updated Profile"
        assert updated.email_from == "updated@example.com"
    
    def test_update_profile_not_found(self, db_session):
        """Test updating non-existent profile."""
        service = ProfileService(db_session)
        
        updated_data = ProfileCreate(name="New Profile")
        result = service.update_profile(999, updated_data)
        
        assert result is None
    
    def test_get_decrypted_profile(self, db_session, sample_profile):
        """Test getting profile with decrypted credentials."""
        from app.security import encryption_service
        
        service = ProfileService(db_session)
        
        # Set encrypted credentials
        sample_profile.smtp_pass = encryption_service.encrypt("super_secret_password")
        sample_profile.twilio_auth_token = encryption_service.encrypt("twilio_secret_token")
        db_session.commit()
        
        decrypted = service.get_decrypted_profile(sample_profile.id)
        
        assert decrypted is not None
        assert decrypted.smtp_pass == "super_secret_password"
        assert decrypted.twilio_auth_token == "twilio_secret_token"
    
    def test_get_decrypted_profile_with_none_credentials(self, db_session, sample_profile):
        """Test getting decrypted profile when credentials are None."""
        service = ProfileService(db_session)
        
        # Ensure credentials are None
        sample_profile.smtp_pass = None
        sample_profile.twilio_auth_token = None
        db_session.commit()
        
        decrypted = service.get_decrypted_profile(sample_profile.id)
        
        assert decrypted is not None
        assert decrypted.smtp_pass is None
        assert decrypted.twilio_auth_token is None
    
    def test_get_decrypted_profile_not_found(self, db_session):
        """Test getting decrypted profile for non-existent profile."""
        service = ProfileService(db_session)
        
        result = service.get_decrypted_profile(999)
        
        assert result is None
    
    def test_update_profile_with_encryption(self, db_session, sample_profile):
        """Test updating profile with new encrypted credentials."""
        service = ProfileService(db_session)
        
        updated_data = ProfileCreate(
            name="Updated Profile",
            email_from="updated@example.com",
            smtp_host="smtp.updated.com",
            smtp_port=465,
            smtp_user="updated_user",
            smtp_pass="new_password",  # Should be encrypted
            twilio_auth_token="new_token"  # Should be encrypted
        )
        
        updated = service.update_profile(sample_profile.id, updated_data)
        
        assert updated is not None
        assert updated.smtp_pass != "new_password"  # Should be encrypted
        assert updated.twilio_auth_token != "new_token"  # Should be encrypted
    
    def test_delete_profile_error_handling(self, db_session, sample_profile):
        """Test delete profile error handling."""
        service = ProfileService(db_session)
        
        # Delete should succeed
        result = service.delete_profile(sample_profile.id)
        assert result is True
        
        # Try to delete again - should return False
        result2 = service.delete_profile(sample_profile.id)
        assert result2 is False
