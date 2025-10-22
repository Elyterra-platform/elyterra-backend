"""
LeadChannel model for proxy email communication (future-ready stub)
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class ChannelType(str, enum.Enum):
    """Channel type enumeration"""
    EMAIL_PROXY = "email_proxy"
    CHAT = "chat"
    DIRECT = "direct"


class LeadChannelModel(BaseModel):
    """LeadChannel model for communication channels"""

    __tablename__ = "lead_channels"

    lead_id = Column(Integer, ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True)
    channel_type = Column(SQLEnum(ChannelType, name='channel_type_enum'), nullable=False)
    proxy_email = Column(String(255), nullable=True)
    status = Column(String(20), default='active', server_default='active', nullable=False)

    # Relationships
    lead = relationship("Lead", back_populates="lead_channels")

    def __repr__(self):
        return f"<LeadChannel(id={self.id}, lead_id={self.lead_id}, type={self.channel_type})>"
