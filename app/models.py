from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class NotificationProfile(Base):
    __tablename__ = "notification_profiles"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email_from = Column(String, nullable=True)
    smtp_host = Column(String, nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_user = Column(String, nullable=True)
    smtp_pass = Column(String, nullable=True)
    twilio_account_sid = Column(String, nullable=True)
    twilio_auth_token = Column(String, nullable=True)
    twilio_from_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    trackers = relationship("Tracker", back_populates="profile")

class Tracker(Base):
    __tablename__ = "trackers"
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    name = Column(String, nullable=True)
    selector = Column(String, nullable=True)
    alert_method = Column(String, nullable=False)  # 'email' | 'sms'
    contact = Column(String, nullable=False)
    currency = Column(String, default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_price = Column(Float, nullable=True)
    profile_id = Column(Integer, ForeignKey("notification_profiles.id"), nullable=True)
    profile = relationship("NotificationProfile", back_populates="trackers")

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True)
    tracker_id = Column(Integer, ForeignKey("trackers.id"), nullable=False)
    checked_at = Column(DateTime, default=datetime.utcnow)
    price = Column(Float, nullable=False)
    delta = Column(Float, nullable=True)
