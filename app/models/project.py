"""
Project model for real estate investment projects
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class AccessLevel(str, enum.Enum):
    """Access level for projects"""
    PUBLIC = "public"
    VERIFIED_ONLY = "verified_only"
    PRE_LAUNCH = "pre_launch"
    INVESTOR_ONLY = "investor_only"


class ContactVisibility(str, enum.Enum):
    """Contact visibility level"""
    HIDDEN = "hidden"
    PROXY = "proxy"
    REVEALED = "revealed"


class ProjectStatus(str, enum.Enum):
    """Project status"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Project(BaseModel):
    """Project model for developer listings"""

    __tablename__ = "projects"

    developer_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Location
    country = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)
    
    # Financial details
    total_investment_required = Column(Numeric(15, 2), nullable=True)
    roi_estimate = Column(Numeric(5, 2), nullable=True)
    currency = Column(String(3), default='EUR', server_default='EUR', nullable=False)
    
    # Property details
    property_type = Column(String(100), nullable=True, index=True)
    size_sqm = Column(Numeric(10, 2), nullable=True)
    tags = Column(JSONB, nullable=True)
    
    # Visibility and access control
    access_level = Column(SQLEnum(AccessLevel, name='access_level_enum', values_callable=lambda x: [e.value for e in x]), default=AccessLevel.PUBLIC, server_default='public', nullable=False)
    contact_visibility = Column(SQLEnum(ContactVisibility, name='contact_visibility_enum', values_callable=lambda x: [e.value for e in x]), default=ContactVisibility.HIDDEN, server_default='hidden', nullable=False)
    visibility_score = Column(Numeric(5, 2), default=0, server_default='0', nullable=False, index=True)
    
    status = Column(SQLEnum(ProjectStatus, name='project_status_enum', values_callable=lambda x: [e.value for e in x]), default=ProjectStatus.DRAFT, server_default='draft', nullable=False, index=True)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    developer = relationship("User", foreign_keys=[developer_id], back_populates="projects")
    documents = relationship("ProjectDocument", back_populates="project", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="project", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="project", cascade="all, delete-orphan")
    project_addons = relationship("ProjectAddon", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, title={self.title}, developer_id={self.developer_id})>"
