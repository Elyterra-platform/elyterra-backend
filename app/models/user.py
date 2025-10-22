"""
User database model with Phase 2 fields for role, tier, and legal compliance
"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class UserRole(str, enum.Enum):
    """User role enumeration"""
    DEVELOPER = "developer"
    INVESTOR = "investor"
    AGENCY = "agency"
    BUYER = "buyer"
    ADMIN = "admin"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TRIAL = "trial"
    NONE = "none"


class User(BaseModel):
    """User model for authentication and profile"""

    __tablename__ = "users"

    # Phase 1 fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, server_default='true', nullable=False)
    is_superuser = Column(Boolean, default=False, server_default='false', nullable=False)
    phone_number = Column(String(20), nullable=True)

    # Phase 2 fields - Role and Tier
    # Use String instead of SQLEnum to avoid enum name vs value serialization issues
    role = Column(String(50), nullable=True, index=True)
    tier = Column(String(50), nullable=True, index=True)
    subscription_status = Column(String(50), default='none', server_default='none', nullable=False)
    subscription_expiry = Column(DateTime, nullable=True)
    verified_status = Column(Boolean, default=False, server_default='false', nullable=False)

    # Phase 2 fields - Legal compliance
    accepted_non_circumvention = Column(Boolean, default=False, server_default='false', nullable=False)
    non_circumvention_accepted_at = Column(DateTime, nullable=True)
    tos_version_accepted = Column(String(20), nullable=True)
    ip_registered = Column(String(45), nullable=True)
    success_fee_policy_version = Column(String(20), nullable=True)

    # Phase 2 fields - Profile
    country = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)
    company_name = Column(String(255), nullable=True)
    tax_id = Column(String(50), nullable=True)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", foreign_keys="[Project.developer_id]", back_populates="developer", cascade="all, delete-orphan")
    user_addons = relationship("UserAddon", back_populates="user", cascade="all, delete-orphan")
    buyer_profile = relationship("BuyerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    initiated_leads = relationship("Lead", foreign_keys="[Lead.initiator_id]", back_populates="initiator")
    received_leads = relationship("Lead", foreign_keys="[Lead.recipient_id]", back_populates="recipient")
    investor_matches = relationship("Match", foreign_keys="[Match.investor_id]", back_populates="investor")
    developer_matches = relationship("Match", foreign_keys="[Match.developer_id]", back_populates="developer")
    agency_listings = relationship("AgencyListing", back_populates="agency", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username} ({self.email}, role={self.role})>"
