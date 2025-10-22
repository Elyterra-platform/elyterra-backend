"""
Database models for Real Estate Investment Platform
"""

from app.models.base import Base, BaseModel
from app.models.user import User, UserRole, SubscriptionStatus
from app.models.subscription import Subscription, SubscriptionRecordStatus
from app.models.project import Project, AccessLevel, ContactVisibility, ProjectStatus
from app.models.project_document import ProjectDocument, DocType
from app.models.lead import Lead, Message, LeadChannel, LeadStatus
from app.models.match import Match, MatchStatus
from app.models.deal import Deal, DealTranche, DealType, DealStatus
from app.models.addon import Addon, UserAddon, ProjectAddon, AddonType, AddonStatus
from app.models.api_request_log import ApiRequestLog
from app.models.agency_listing import AgencyListing
from app.models.buyer_profile import BuyerProfile
from app.models.lead_channel import LeadChannelModel, ChannelType

__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    # User and related enums
    "User",
    "UserRole",
    "SubscriptionStatus",
    # Subscription
    "Subscription",
    "SubscriptionRecordStatus",
    # Project and related
    "Project",
    "ProjectDocument",
    "AccessLevel",
    "ContactVisibility",
    "ProjectStatus",
    "DocType",
    # Lead and Message
    "Lead",
    "Message",
    "LeadChannel",
    "LeadStatus",
    # Match
    "Match",
    "MatchStatus",
    # Deal
    "Deal",
    "DealTranche",
    "DealType",
    "DealStatus",
    # Addons
    "Addon",
    "UserAddon",
    "ProjectAddon",
    "AddonType",
    "AddonStatus",
    # API Request Log
    "ApiRequestLog",
    # Agency Listing
    "AgencyListing",
    # Buyer Profile
    "BuyerProfile",
    # Lead Channel
    "LeadChannelModel",
    "ChannelType",
]
