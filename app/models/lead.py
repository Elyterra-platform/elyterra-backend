"""
Lead and Message models for communication tracking
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class LeadChannel(str, enum.Enum):
    """Lead channel enumeration"""
    CHAT = "chat"
    EMAIL_PROXY = "email_proxy"
    PLATFORM = "platform"
    DIRECT = "direct"


class LeadStatus(str, enum.Enum):
    """Lead status enumeration"""
    PENDING = "pending"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    CLOSED = "closed"


class Lead(BaseModel):
    """Lead model for tracking proof of introduction"""

    __tablename__ = "leads"

    initiator_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True, index=True)
    listing_id = Column(Integer, ForeignKey('agency_listings.id', ondelete='CASCADE'), nullable=True, index=True)
    
    channel = Column(SQLEnum(LeadChannel, name='lead_channel_enum'), nullable=False)
    status = Column(SQLEnum(LeadStatus, name='lead_status_enum'), default=LeadStatus.PENDING, server_default='pending', nullable=False, index=True)
    
    # Legal evidence tracking
    first_contact_ip = Column(String(45), nullable=True)
    
    # Relationships
    initiator = relationship("User", foreign_keys=[initiator_id], back_populates="initiated_leads")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_leads")
    project = relationship("Project", back_populates="leads")
    listing = relationship("AgencyListing", back_populates="leads")
    messages = relationship("Message", back_populates="lead", cascade="all, delete-orphan")
    deals = relationship("Deal", back_populates="lead", cascade="all, delete-orphan")
    lead_channels = relationship("LeadChannelModel", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lead(id={self.id}, initiator_id={self.initiator_id}, recipient_id={self.recipient_id})>"


class Message(BaseModel):
    """Message model for message retention (≥12 months for legal compliance)"""

    __tablename__ = "messages"

    lead_id = Column(Integer, ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, server_default='false', nullable=False)
    
    # Legal evidence tracking
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, lead_id={self.lead_id})>"
