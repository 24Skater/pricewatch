from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class NotificationProfile(Base):
    __tablename__ = "notification_profiles"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    email_from = Column(String(255), nullable=True)
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_user = Column(String(255), nullable=True)
    smtp_pass = Column(Text, nullable=True)  # Encrypted
    twilio_account_sid = Column(String(255), nullable=True)
    twilio_auth_token = Column(Text, nullable=True)  # Encrypted
    twilio_from_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    trackers = relationship("Tracker", back_populates="profile")

class Tracker(Base):
    __tablename__ = "trackers"
    id = Column(Integer, primary_key=True)
    url = Column(String(2000), nullable=False, index=True)
    name = Column(String(500), nullable=True)
    selector = Column(String(1000), nullable=True)
    alert_method = Column(String(10), nullable=False, index=True)  # 'email' | 'sms'
    contact = Column(String(255), nullable=False)
    currency = Column(String(3), default="USD", index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_price = Column(Float, nullable=True, index=True)
    profile_id = Column(Integer, ForeignKey("notification_profiles.id"), nullable=True, index=True)
    profile = relationship("NotificationProfile", back_populates="trackers")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_tracker_active_created', 'is_active', 'created_at'),
        Index('idx_tracker_method_active', 'alert_method', 'is_active'),
    )

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True)
    tracker_id = Column(Integer, ForeignKey("trackers.id"), nullable=False, index=True)
    checked_at = Column(DateTime, default=datetime.utcnow, index=True)
    price = Column(Float, nullable=False, index=True)
    delta = Column(Float, nullable=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_price_history_tracker_checked', 'tracker_id', 'checked_at'),
        Index('idx_price_history_checked_price', 'checked_at', 'price'),
    )
