"""
AgencyListing model for real estate agency property listings
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.project import AccessLevel, ContactVisibility, ProjectStatus


class AgencyListing(BaseModel):
    """AgencyListing model for agency property listings"""

    __tablename__ = "agency_listings"

    agency_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Location
    country = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)

    # Pricing
    price = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='EUR', server_default='EUR', nullable=False)

    # Property details
    property_type = Column(String(100), nullable=True, index=True)
    size_sqm = Column(Numeric(10, 2), nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    amenities = Column(JSONB, nullable=True)
    media_urls = Column(JSONB, nullable=True)

    # Visibility and access control (reuse enums from project model)
    access_level = Column(SQLEnum(AccessLevel, name='access_level_enum', create_type=False), default=AccessLevel.PUBLIC, server_default='public', nullable=False)
    contact_visibility = Column(SQLEnum(ContactVisibility, name='contact_visibility_enum', create_type=False), default=ContactVisibility.HIDDEN, server_default='hidden', nullable=False)
    visibility_score = Column(Numeric(5, 2), default=0, server_default='0', nullable=False, index=True)

    status = Column(SQLEnum(ProjectStatus, name='project_status_enum', create_type=False), default=ProjectStatus.DRAFT, server_default='draft', nullable=False, index=True)

    # Relationships
    agency = relationship("User", back_populates="agency_listings")
    leads = relationship("Lead", back_populates="listing", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AgencyListing(id={self.id}, title={self.title}, agency_id={self.agency_id})>"
