"""
BuyerProfile model for buyer preferences (future-ready stub)
"""

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class BuyerProfile(BaseModel):
    """BuyerProfile model for buyer preferences and investment capacity"""

    __tablename__ = "buyer_profiles"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    preferences = Column(JSONB, nullable=True)
    investment_capacity = Column(Numeric(15, 2), nullable=True)
    risk_tolerance = Column(String(20), nullable=True)

    # Relationships
    user = relationship("User", back_populates="buyer_profile")

    __table_args__ = (
        UniqueConstraint('user_id', name='uq_buyer_profiles_user_id'),
    )

    def __repr__(self):
        return f"<BuyerProfile(id={self.id}, user_id={self.user_id})>"
