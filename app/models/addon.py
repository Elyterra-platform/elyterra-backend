"""
Addon models for add-on services (Verification, Visibility Boost, Intro Package)
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class AddonType(str, enum.Enum):
    """Addon type enumeration"""
    VERIFICATION = "verification"
    VISIBILITY_BOOST = "visibility_boost"
    INTRO_PACKAGE = "intro_package"
    OTHER = "other"


class AddonStatus(str, enum.Enum):
    """Addon status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Addon(BaseModel):
    """Addon model for available add-on services"""

    __tablename__ = "addons"

    addon_type = Column(SQLEnum(AddonType, name='addon_type_enum'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='EUR', server_default='EUR', nullable=False)
    duration_days = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, server_default='true', nullable=False, index=True)

    # Relationships
    user_addons = relationship("UserAddon", back_populates="addon", cascade="all, delete-orphan")
    project_addons = relationship("ProjectAddon", back_populates="addon", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Addon(id={self.id}, name={self.name}, type={self.addon_type})>"


class UserAddon(BaseModel):
    """UserAddon model for user-level add-on purchases"""

    __tablename__ = "user_addons"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    addon_id = Column(Integer, ForeignKey('addons.id', ondelete='CASCADE'), nullable=False, index=True)
    status = Column(SQLEnum(AddonStatus, name='addon_status_enum'), default=AddonStatus.PENDING, server_default='pending', nullable=False, index=True)
    
    purchased_at = Column(DateTime, nullable=False)
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    payment_amount = Column(Numeric(10, 2), nullable=False)
    payment_currency = Column(String(3), nullable=False)

    # Relationships
    user = relationship("User", back_populates="user_addons")
    addon = relationship("Addon", back_populates="user_addons")

    def __repr__(self):
        return f"<UserAddon(id={self.id}, user_id={self.user_id}, addon_id={self.addon_id})>"


class ProjectAddon(BaseModel):
    """ProjectAddon model for project-level add-on purchases"""

    __tablename__ = "project_addons"

    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    addon_id = Column(Integer, ForeignKey('addons.id', ondelete='CASCADE'), nullable=False, index=True)
    status = Column(SQLEnum(AddonStatus, name='addon_status_enum', create_type=False), default=AddonStatus.PENDING, server_default='pending', nullable=False, index=True)
    
    purchased_at = Column(DateTime, nullable=False)
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    visibility_boost_amount = Column(Numeric(5, 2), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="project_addons")
    addon = relationship("Addon", back_populates="project_addons")

    def __repr__(self):
        return f"<ProjectAddon(id={self.id}, project_id={self.project_id}, addon_id={self.addon_id})>"
