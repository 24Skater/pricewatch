import os, smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from twilio.rest import Client

FROM_EMAIL = os.getenv("FROM_EMAIL", "alerts@example.com")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

def send_email(to_email: str, subject: str, body: str):
    if not SMTP_HOST:
        print("[WARN] SMTP not configured; skipping email.")
        return
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Pricewatch", FROM_EMAIL))
    msg["To"] = to_email
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USER:
            server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

def send_sms(to_number: str, body: str):
    if not TWILIO_ACCOUNT_SID:
        print("[WARN] Twilio not configured; skipping SMS.")
        return
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        to=to_number,
        from_=TWILIO_FROM_NUMBER,
        body=body,
    )
