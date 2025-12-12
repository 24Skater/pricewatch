"""Tracker business logic service."""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models import Tracker, PriceHistory, NotificationProfile
from app.schemas import TrackerCreate, TrackerOut
from app.scraper import get_price
from app.services.base import BaseService
from app.services.notification_service import notification_service
from app.exceptions import ValidationError, ScrapingError, DatabaseError
from app.security import input_validator


class TrackerService(BaseService[Tracker]):
    """Service for tracker business logic."""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def create_tracker(self, tracker_data: TrackerCreate) -> Tracker:
        """Create a new tracker."""
        try:
            # Validate inputs
            if not input_validator.validate_url(str(tracker_data.url)):
                raise ValidationError("Invalid URL format")
            
            if tracker_data.alert_method == "email":
                if not input_validator.validate_email(tracker_data.contact):
                    raise ValidationError("Invalid email format")
            elif tracker_data.alert_method == "sms":
                if not input_validator.validate_phone_number(tracker_data.contact):
                    raise ValidationError("Invalid phone number format")
            
            # Create tracker
            tracker = Tracker(
                url=str(tracker_data.url),
                alert_method=tracker_data.alert_method,
                contact=tracker_data.contact,
                selector=tracker_data.selector,
                name=tracker_data.name,
            )
            
            # Set profile if provided
            if tracker_data.profile_id:
                profile = self.db.query(NotificationProfile).filter(
                    NotificationProfile.id == tracker_data.profile_id
                ).first()
                if not profile:
                    raise ValidationError("Profile not found")
                tracker.profile = profile
            
            # Try to get initial price
            try:
                price, currency, title = get_price(tracker.url, tracker.selector)
                tracker.currency = currency or "USD"
                tracker.last_price = price
                if title and not tracker.name:
                    tracker.name = title[:200]
            except Exception as e:
                self.logger.warning(f"Initial price fetch failed for {tracker.url}: {e}")
            
            self.db.add(tracker)
            self.db.commit()
            self.db.refresh(tracker)
            
            # Record initial price if available
            if tracker.last_price is not None:
                price_history = PriceHistory(
                    tracker_id=tracker.id,
                    price=tracker.last_price,
                    delta=None
                )
                self.db.add(price_history)
                self.db.commit()
            
            self.logger.info(f"Created tracker {tracker.id} for {tracker.url}")
            return tracker
            
        except Exception as e:
            self._rollback()
            self.logger.error(f"Failed to create tracker: {e}")
            raise DatabaseError(f"Failed to create tracker: {e}")
    
    def get_tracker(self, tracker_id: int) -> Optional[Tracker]:
        """Get a tracker by ID."""
        return self.db.query(Tracker).filter(Tracker.id == tracker_id).first()
    
    def get_all_trackers(self) -> List[Tracker]:
        """Get all trackers."""
        return self.db.query(Tracker).order_by(Tracker.created_at.desc()).all()
    
    def update_tracker(self, tracker_id: int, tracker_data: TrackerCreate) -> Optional[Tracker]:
        """Update a tracker."""
        tracker = self.get_tracker(tracker_id)
        if not tracker:
            return None
        
        try:
            # Validate inputs
            if not input_validator.validate_url(str(tracker_data.url)):
                raise ValidationError("Invalid URL format")
            
            if tracker_data.alert_method == "email":
                if not input_validator.validate_email(tracker_data.contact):
                    raise ValidationError("Invalid email format")
            elif tracker_data.alert_method == "sms":
                if not input_validator.validate_phone_number(tracker_data.contact):
                    raise ValidationError("Invalid phone number format")
            
            # Update tracker fields
            tracker.url = str(tracker_data.url)
            tracker.name = tracker_data.name
            tracker.selector = tracker_data.selector
            tracker.alert_method = tracker_data.alert_method
            tracker.contact = tracker_data.contact
            
            # Update profile
            if tracker_data.profile_id:
                profile = self.db.query(NotificationProfile).filter(
                    NotificationProfile.id == tracker_data.profile_id
                ).first()
                if not profile:
                    raise ValidationError("Profile not found")
                tracker.profile = profile
            else:
                tracker.profile = None
            
            self.db.add(tracker)
            self.db.commit()
            self.db.refresh(tracker)
            
            self.logger.info(f"Updated tracker {tracker.id}")
            return tracker
            
        except Exception as e:
            self._rollback()
            self.logger.error(f"Failed to update tracker {tracker_id}: {e}")
            raise DatabaseError(f"Failed to update tracker: {e}")
    
    def delete_tracker(self, tracker_id: int) -> bool:
        """Delete a tracker and its price history."""
        tracker = self.get_tracker(tracker_id)
        if not tracker:
            return False
        
        try:
            # Delete price history first
            self.db.query(PriceHistory).filter(
                PriceHistory.tracker_id == tracker_id
            ).delete()
            
            # Delete tracker
            self.db.delete(tracker)
            self.db.commit()
            
            self.logger.info(f"Deleted tracker {tracker_id}")
            return True
            
        except Exception as e:
            self._rollback()
            self.logger.error(f"Failed to delete tracker {tracker_id}: {e}")
            raise DatabaseError(f"Failed to delete tracker: {e}")
    
    def refresh_tracker_price(self, tracker_id: int) -> Tuple[Optional[float], Optional[str]]:
        """Refresh price for a tracker."""
        tracker = self.get_tracker(tracker_id)
        if not tracker:
            raise ValidationError("Tracker not found")
        
        try:
            price, currency, _ = get_price(tracker.url, tracker.selector)
            
            if price is None:
                raise ScrapingError("Could not parse price from page")
            
            # Calculate delta
            delta = None
            if tracker.last_price is not None:
                delta = round(price - tracker.last_price, 2)
            
            # Update tracker if price changed
            if tracker.last_price is None or abs(price - tracker.last_price) > 1e-6:
                # Record price history
                price_history = PriceHistory(
                    tracker_id=tracker.id,
                    price=price,
                    delta=delta
                )
                self.db.add(price_history)
                
                # Update tracker
                tracker.last_price = price
                tracker.currency = tracker.currency or (currency or "USD")
                self.db.add(tracker)
                self.db.commit()
                
                # Send notification if price changed significantly
                if delta is not None and abs(delta) > 1e-6:
                    notification_service.send_price_alert(tracker, price, delta)
                
                self.logger.info(f"Updated price for tracker {tracker_id}: ${price}")
            
            return price, currency
            
        except Exception as e:
            self.logger.error(f"Failed to refresh price for tracker {tracker_id}: {e}")
            raise ScrapingError(f"Failed to refresh price: {e}")
    
