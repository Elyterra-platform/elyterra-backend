"""
Deal and DealTranche models for transaction tracking with success fee calculation
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class DealType(str, enum.Enum):
    """Deal type enumeration"""
    CAPITAL_RAISE = "capital_raise"
    ASSET_SALE = "asset_sale"
    AGENCY_REFERRAL = "agency_referral"


class DealStatus(str, enum.Enum):
    """Deal status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAID = "paid"
    DISPUTED = "disputed"


class Deal(BaseModel):
    """Deal model for tracking completed transactions"""

    __tablename__ = "deals"

    lead_id = Column(Integer, ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True)
    deal_type = Column(SQLEnum(DealType, name='deal_type_enum'), nullable=False)
    total_value = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='EUR', server_default='EUR', nullable=False)
    
    # Success fee system with rate locking
    success_fee_rate_locked = Column(Numeric(5, 4), nullable=False)  # e.g., 0.0300 = 3%
    success_fee_calculated = Column(Numeric(10, 2), nullable=True)
    success_fee_minimum = Column(Numeric(10, 2), nullable=False)
    locked_tier = Column(String(50), nullable=False)  # Tier at lead creation
    locked_at = Column(DateTime, nullable=False)
    
    status = Column(SQLEnum(DealStatus, name='deal_status_enum'), default=DealStatus.PENDING, server_default='pending', nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    payment_received_at = Column(DateTime, nullable=True)
    disputed = Column(Boolean, default=False, server_default='false', nullable=False)

    # Relationships
    lead = relationship("Lead", back_populates="deals")
    tranches = relationship("DealTranche", back_populates="deal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Deal(id={self.id}, lead_id={self.lead_id}, total_value={self.total_value}, status={self.status})>"


class DealTranche(BaseModel):
    """DealTranche model for multi-tranche deals"""

    __tablename__ = "deal_tranches"

    deal_id = Column(Integer, ForeignKey('deals.id', ondelete='CASCADE'), nullable=False, index=True)
    tranche_number = Column(Integer, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='EUR', server_default='EUR', nullable=False)
    fx_rate_to_eur = Column(Numeric(10, 6), nullable=True)
    amount_eur_cached = Column(Numeric(15, 2), nullable=True)
    payment_date = Column(DateTime, nullable=True)

    # Relationships
    deal = relationship("Deal", back_populates="tranches")

    def __repr__(self):
        return f"<DealTranche(id={self.id}, deal_id={self.deal_id}, tranche={self.tranche_number})>"
