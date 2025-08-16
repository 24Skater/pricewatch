import os, smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from twilio.rest import Client

ENV_SMTP = {
    "email_from": os.getenv("FROM_EMAIL", "alerts@example.com"),
    "smtp_host": os.getenv("SMTP_HOST", ""),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None,
    "smtp_user": os.getenv("SMTP_USER", ""),
    "smtp_pass": os.getenv("SMTP_PASS", ""),
}
ENV_TWILIO = {
    "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
    "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
    "twilio_from_number": os.getenv("TWILIO_FROM_NUMBER", ""),
}

def _smtp_config(profile):
    if profile:
        return {
            "email_from": profile.email_from or ENV_SMTP["email_from"],
            "smtp_host": profile.smtp_host or ENV_SMTP["smtp_host"],
            "smtp_port": profile.smtp_port or ENV_SMTP["smtp_port"] or 587,
            "smtp_user": profile.smtp_user or ENV_SMTP["smtp_user"],
            "smtp_pass": profile.smtp_pass or ENV_SMTP["smtp_pass"]
        }
    return ENV_SMTP

def _twilio_config(profile):
    if profile:
        return {
            "twilio_account_sid": profile.twilio_account_sid or ENV_TWILIO["twilio_account_sid"],
            "twilio_auth_token": profile.twilio_auth_token or ENV_TWILIO["twilio_auth_token"],
            "twilio_from_number": profile.twilio_from_number or ENV_TWILIO["twilio_from_number"]
        }
    return ENV_TWILIO

def send_email(to_email: str, subject: str, body: str, profile=None):
    cfg = _smtp_config(profile)
    if not cfg["smtp_host"]:
        print("[WARN] SMTP not configured; skipping email.")
        return
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Pricewatch", cfg["email_from"]))
    msg["To"] = to_email
    with smtplib.SMTP(cfg["smtp_host"], int(cfg["smtp_port"])) as server:
        server.starttls()
        if cfg["smtp_user"]:
            server.login(cfg["smtp_user"], cfg["smtp_pass"]
            )
        server.send_message(msg)

def send_sms(to_number: str, body: str, profile=None):
    cfg = _twilio_config(profile)
    if not cfg["twilio_account_sid"]:
        print("[WARN] Twilio not configured; skipping SMS.")
        return
    client = Client(cfg["twilio_account_sid"], cfg["twilio_auth_token"])
    client.messages.create(to=to_number, from_=cfg["twilio_from_number"], body=body)
