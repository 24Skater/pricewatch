import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from twilio.rest import Client
from .config import settings
from .logging_config import get_logger
from .security import encryption_service

logger = get_logger(__name__)

ENV_SMTP = {
    "email_from": settings.from_email,
    "smtp_host": settings.smtp_host,
    "smtp_port": settings.smtp_port,
    "smtp_user": settings.smtp_user,
    "smtp_pass": settings.smtp_pass,
}
ENV_TWILIO = {
    "twilio_account_sid": settings.twilio_account_sid,
    "twilio_auth_token": settings.twilio_auth_token,
    "twilio_from_number": settings.twilio_from_number,
}

def _smtp_config(profile):
    """Get SMTP configuration, decrypting profile credentials if needed."""
    if profile:
        # Decrypt profile credentials
        smtp_pass = None
        if profile.smtp_pass:
            try:
                smtp_pass = encryption_service.decrypt(profile.smtp_pass)
            except Exception as e:
                logger.warning(f"Failed to decrypt SMTP password for profile {profile.id}: {e}")
        
        return {
            "email_from": profile.email_from or ENV_SMTP["email_from"],
            "smtp_host": profile.smtp_host or ENV_SMTP["smtp_host"],
            "smtp_port": profile.smtp_port or ENV_SMTP["smtp_port"] or 587,
            "smtp_user": profile.smtp_user or ENV_SMTP["smtp_user"],
            "smtp_pass": smtp_pass or ENV_SMTP["smtp_pass"]
        }
    return ENV_SMTP

def _twilio_config(profile):
    """Get Twilio configuration, decrypting profile credentials if needed."""
    if profile:
        # Decrypt profile credentials
        twilio_auth_token = None
        if profile.twilio_auth_token:
            try:
                twilio_auth_token = encryption_service.decrypt(profile.twilio_auth_token)
            except Exception as e:
                logger.warning(f"Failed to decrypt Twilio auth token for profile {profile.id}: {e}")
        
        return {
            "twilio_account_sid": profile.twilio_account_sid or ENV_TWILIO["twilio_account_sid"],
            "twilio_auth_token": twilio_auth_token or ENV_TWILIO["twilio_auth_token"],
            "twilio_from_number": profile.twilio_from_number or ENV_TWILIO["twilio_from_number"]
        }
    return ENV_TWILIO

def send_email(to_email: str, subject: str, body: str, profile=None):
    """Send email notification."""
    try:
        cfg = _smtp_config(profile)
        if not cfg["smtp_host"]:
            logger.warning("SMTP not configured; skipping email.")
            return
        
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = formataddr(("Pricewatch", cfg["email_from"]))
        msg["To"] = to_email
        
        with smtplib.SMTP(cfg["smtp_host"], int(cfg["smtp_port"])) as server:
            server.starttls()
            if cfg["smtp_user"]:
                server.login(cfg["smtp_user"], cfg["smtp_pass"])
            server.send_message(msg)
        
        logger.info(f"Email sent to {to_email}")
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise

def send_sms(to_number: str, body: str, profile=None):
    """Send SMS notification."""
    try:
        cfg = _twilio_config(profile)
        if not cfg["twilio_account_sid"]:
            logger.warning("Twilio not configured; skipping SMS.")
            return
        
        client = Client(cfg["twilio_account_sid"], cfg["twilio_auth_token"])
        client.messages.create(to=to_number, from_=cfg["twilio_from_number"], body=body)
        
        logger.info(f"SMS sent to {to_number}")
        
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_number}: {e}")
        raise
