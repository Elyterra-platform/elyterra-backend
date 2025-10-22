"""
Subscription model for monthly subscription tracking
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class SubscriptionRecordStatus(str, enum.Enum):
    """Subscription record status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class Subscription(BaseModel):
    """Subscription model for tracking user subscriptions"""

    __tablename__ = "subscriptions"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    tier = Column(String(50), nullable=False)
    status = Column(SQLEnum(SubscriptionRecordStatus, name='subscription_record_status_enum'), nullable=False, index=True)
    start_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=True, index=True)
    monthly_fee = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='EUR', server_default='EUR', nullable=False)
    
    # Stripe integration placeholders
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    
    auto_renew = Column(Boolean, default=True, server_default='true', nullable=False)
    grace_period_ends = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, tier={self.tier}, status={self.status})>"
