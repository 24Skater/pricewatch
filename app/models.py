from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Tracker(Base):
    __tablename__ = "trackers"
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    name = Column(String, nullable=True)
    selector = Column(String, nullable=True)
    alert_method = Column(String, nullable=False)  # 'email' or 'sms'
    contact = Column(String, nullable=False)       # email or phone
    currency = Column(String, default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_price = Column(Float, nullable=True)

    history = relationship("PriceHistory", back_populates="tracker", cascade="all, delete-orphan")

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True)
    tracker_id = Column(Integer, ForeignKey("trackers.id"), nullable=False)
    checked_at = Column(DateTime, default=datetime.utcnow)
    price = Column(Float, nullable=False)
    delta = Column(Float, nullable=True)

    tracker = relationship("Tracker", back_populates="history")
