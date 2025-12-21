"""Notification service for sending alerts via email and SMS."""

from typing import Optional
from app.models import Tracker, NotificationProfile
from app.alerts import send_email as _send_email, send_sms as _send_sms
from app.logging_config import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Service for handling all notification logic.
    
    This is the single source of truth for sending notifications.
    Both TrackerService and SchedulerService delegate to this class.
    """
    
    def send_price_alert(
        self,
        tracker: Tracker,
        price: float,
        delta: float
    ) -> bool:
        """Send price change notification for a tracker.
        
        Args:
            tracker: The tracker that had a price change
            price: The new price
            delta: The price change (positive = increase, negative = decrease)
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            sign = "decreased" if delta < 0 else "increased"
            subject = f"Price {sign}: {tracker.name or tracker.url}"
            body = (
                f"The price has {sign} by ${abs(delta):.2f}\n"
                f"Current price: ${price:.2f}\n"
                f"URL: {tracker.url}\n"
            )
            
            if tracker.alert_method == "email":
                self.send_email(
                    to_email=tracker.contact,
                    subject=subject,
                    body=body,
                    profile=tracker.profile
                )
            else:
                self.send_sms(
                    to_number=tracker.contact,
                    body=f"{subject}\n{body}",
                    profile=tracker.profile
                )
            
            logger.info(f"Sent {tracker.alert_method} notification for tracker {tracker.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification for tracker {tracker.id}: {e}")
            return False
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        profile: Optional[NotificationProfile] = None
    ) -> None:
        """Send email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: Email body content
            profile: Optional notification profile for custom SMTP settings
            
        Raises:
            Exception: If email sending fails
        """
        _send_email(to_email, subject, body, profile=profile)
    
    def send_sms(
        self,
        to_number: str,
        body: str,
        profile: Optional[NotificationProfile] = None
    ) -> None:
        """Send SMS notification.
        
        Args:
            to_number: Recipient phone number
            body: SMS message content
            profile: Optional notification profile for custom Twilio settings
            
        Raises:
            Exception: If SMS sending fails
        """
        _send_sms(to_number, body, profile=profile)


# Singleton instance for convenience
notification_service = NotificationService()

