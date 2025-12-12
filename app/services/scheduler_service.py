"""Scheduler service for background tasks."""

from typing import List
from sqlalchemy.orm import Session
from app.models import Tracker, PriceHistory
from app.scraper import get_price
from app.services.base import BaseService
from app.services.notification_service import notification_service
from app.exceptions import ScrapingError
from app.config import settings


class SchedulerService(BaseService[Tracker]):
    """Service for scheduled background tasks."""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def poll_all_trackers(self) -> None:
        """Poll all active trackers for price updates."""
        try:
            trackers = self.db.query(Tracker).filter(Tracker.is_active == True).all()
            self.logger.info(f"Polling {len(trackers)} active trackers")
            
            for tracker in trackers:
                try:
                    self._poll_tracker(tracker)
                except Exception as e:
                    self.logger.error(f"Failed to poll tracker {tracker.id}: {e}")
                    continue
            
            self.logger.info("Completed polling all trackers")
            
        except Exception as e:
            self.logger.error(f"Failed to poll trackers: {e}")
            raise
    
    def _poll_tracker(self, tracker: Tracker) -> None:
        """Poll a single tracker for price updates."""
        try:
            price, currency, title = get_price(tracker.url, tracker.selector)
            
            if price is None:
                self.logger.warning(f"No price found for tracker {tracker.id} ({tracker.url})")
                return
            
            # Calculate delta
            delta = None
            if tracker.last_price is not None:
                delta = round(price - tracker.last_price, 2)
            
            # Update if price changed
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
                if title and not tracker.name:
                    tracker.name = title[:200]
                
                self.db.add(tracker)
                self.db.commit()
                
                # Send notification if price changed significantly
                if delta is not None and abs(delta) > 1e-6:
                    notification_service.send_price_alert(tracker, price, delta)
                
                self.logger.info(f"Updated price for tracker {tracker.id}: ${price} (delta: ${delta})")
            else:
                self.logger.debug(f"No price change for tracker {tracker.id}")
                
        except Exception as e:
            self.logger.error(f"Failed to poll tracker {tracker.id}: {e}")
            raise ScrapingError(f"Failed to poll tracker: {e}")
    
