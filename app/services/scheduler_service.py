"""Scheduler service for background tasks."""

from typing import List
from sqlalchemy.orm import Session
from app.models import Tracker, PriceHistory
from app.scraper import get_price
from app.alerts import send_email, send_sms
from app.exceptions import ScrapingError
from app.logging_config import get_logger
from app.config import settings

logger = get_logger(__name__)


class SchedulerService:
    """Service for scheduled background tasks."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def poll_all_trackers(self) -> None:
        """Poll all active trackers for price updates."""
        try:
            trackers = self.db.query(Tracker).filter(Tracker.is_active == True).all()
            logger.info(f"Polling {len(trackers)} active trackers")
            
            for tracker in trackers:
                try:
                    self._poll_tracker(tracker)
                except Exception as e:
                    logger.error(f"Failed to poll tracker {tracker.id}: {e}")
                    continue
            
            logger.info("Completed polling all trackers")
            
        except Exception as e:
            logger.error(f"Failed to poll trackers: {e}")
            raise
    
    def _poll_tracker(self, tracker: Tracker) -> None:
        """Poll a single tracker for price updates."""
        try:
            price, currency, title = get_price(tracker.url, tracker.selector)
            
            if price is None:
                logger.warning(f"No price found for tracker {tracker.id} ({tracker.url})")
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
                    self._send_price_notification(tracker, price, delta)
                
                logger.info(f"Updated price for tracker {tracker.id}: ${price} (delta: ${delta})")
            else:
                logger.debug(f"No price change for tracker {tracker.id}")
                
        except Exception as e:
            logger.error(f"Failed to poll tracker {tracker.id}: {e}")
            raise ScrapingError(f"Failed to poll tracker: {e}")
    
    def _send_price_notification(self, tracker: Tracker, price: float, delta: float) -> None:
        """Send price change notification."""
        try:
            sign = "decreased" if delta < 0 else "increased"
            subject = f"Price {sign}: {tracker.name or tracker.url}"
            body = (
                f"The price has {sign} by ${abs(delta):.2f}\n"
                f"Current price: ${price:.2f}\n"
                f"URL: {tracker.url}\n"
            )
            
            if tracker.alert_method == "email":
                send_email(tracker.contact, subject, body, profile=tracker.profile)
            else:
                send_sms(tracker.contact, subject + "\n" + body, profile=tracker.profile)
            
            logger.info(f"Sent {tracker.alert_method} notification for tracker {tracker.id}")
            
        except Exception as e:
            logger.error(f"Failed to send notification for tracker {tracker.id}: {e}")
            # Don't raise exception for notification failures
