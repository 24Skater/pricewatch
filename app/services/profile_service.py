"""Notification profile business logic service."""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import NotificationProfile
from app.schemas import ProfileCreate
from app.exceptions import ValidationError, DatabaseError
from app.logging_config import get_logger
from app.security import input_validator, encryption_service

logger = get_logger(__name__)


class ProfileService:
    """Service for notification profile business logic."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_profile(self, profile_data: ProfileCreate) -> NotificationProfile:
        """Create a new notification profile."""
        try:
            # Validate inputs
            if not profile_data.name or len(profile_data.name.strip()) < 1:
                raise ValidationError("Profile name is required")
            
            if profile_data.email_from and not input_validator.validate_email(profile_data.email_from):
                raise ValidationError("Invalid email format")
            
            # Encrypt sensitive data
            encrypted_data = {}
            for field in ['smtp_pass', 'twilio_auth_token']:
                value = getattr(profile_data, field)
                if value:
                    encrypted_data[field] = encryption_service.encrypt(value)
            
            # Create profile
            profile_dict = profile_data.model_dump()
            for field, encrypted_value in encrypted_data.items():
                profile_dict[field] = encrypted_value
            
            profile = NotificationProfile(**profile_dict)
            
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info(f"Created profile {profile.id}: {profile.name}")
            return profile
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create profile: {e}")
            raise DatabaseError(f"Failed to create profile: {e}")
    
    def get_profile(self, profile_id: int) -> Optional[NotificationProfile]:
        """Get a profile by ID."""
        return self.db.query(NotificationProfile).filter(
            NotificationProfile.id == profile_id
        ).first()
    
    def get_all_profiles(self) -> List[NotificationProfile]:
        """Get all profiles."""
        return self.db.query(NotificationProfile).order_by(
            NotificationProfile.created_at.desc()
        ).all()
    
    def update_profile(self, profile_id: int, profile_data: ProfileCreate) -> Optional[NotificationProfile]:
        """Update a profile."""
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        try:
            # Validate inputs
            if not profile_data.name or len(profile_data.name.strip()) < 1:
                raise ValidationError("Profile name is required")
            
            if profile_data.email_from and not input_validator.validate_email(profile_data.email_from):
                raise ValidationError("Invalid email format")
            
            # Update profile fields
            profile.name = profile_data.name
            profile.email_from = profile_data.email_from
            profile.smtp_host = profile_data.smtp_host
            profile.smtp_port = profile_data.smtp_port
            profile.smtp_user = profile_data.smtp_user
            profile.twilio_account_sid = profile_data.twilio_account_sid
            profile.twilio_from_number = profile_data.twilio_from_number
            
            # Encrypt sensitive data if provided
            if profile_data.smtp_pass:
                profile.smtp_pass = encryption_service.encrypt(profile_data.smtp_pass)
            if profile_data.twilio_auth_token:
                profile.twilio_auth_token = encryption_service.encrypt(profile_data.twilio_auth_token)
            
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info(f"Updated profile {profile.id}")
            return profile
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update profile {profile_id}: {e}")
            raise DatabaseError(f"Failed to update profile: {e}")
    
    def delete_profile(self, profile_id: int) -> bool:
        """Delete a profile."""
        profile = self.get_profile(profile_id)
        if not profile:
            return False
        
        try:
            self.db.delete(profile)
            self.db.commit()
            
            logger.info(f"Deleted profile {profile_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete profile {profile_id}: {e}")
            raise DatabaseError(f"Failed to delete profile: {e}")
    
    def get_decrypted_profile(self, profile_id: int) -> Optional[NotificationProfile]:
        """Get a profile with decrypted sensitive data."""
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        # Create a copy with decrypted data
        decrypted_profile = NotificationProfile(
            id=profile.id,
            name=profile.name,
            email_from=profile.email_from,
            smtp_host=profile.smtp_host,
            smtp_port=profile.smtp_port,
            smtp_user=profile.smtp_user,
            smtp_pass=encryption_service.decrypt(profile.smtp_pass) if profile.smtp_pass else None,
            twilio_account_sid=profile.twilio_account_sid,
            twilio_auth_token=encryption_service.decrypt(profile.twilio_auth_token) if profile.twilio_auth_token else None,
            twilio_from_number=profile.twilio_from_number,
            created_at=profile.created_at
        )
        
        return decrypted_profile
