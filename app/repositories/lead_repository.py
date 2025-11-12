"""
Lead Repository
Handles database operations for leads and messages
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from typing import Optional, List
from app.models.lead import Lead, Message


class LeadRepository:
    """Repository for lead database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, lead_data: dict) -> Lead:
        """Create a new lead"""
        lead = Lead(**lead_data)
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def find_by_id(self, lead_id: int, include_relationships: bool = True) -> Optional[Lead]:
        """Find lead by ID"""
        query = self.db.query(Lead)

        if include_relationships:
            query = query.options(
                joinedload(Lead.initiator),
                joinedload(Lead.recipient),
                joinedload(Lead.project)
            )

        return query.filter(Lead.id == lead_id).first()

    def find_existing_lead(
        self,
        initiator_id: int,
        recipient_id: int,
        project_id: Optional[int] = None,
        listing_id: Optional[int] = None
    ) -> Optional[Lead]:
        """
        Check if lead already exists between two users

        Args:
            initiator_id: Investor/buyer ID
            recipient_id: Developer/agency ID
            project_id: Optional project ID
            listing_id: Optional listing ID

        Returns:
            Existing lead or None
        """
        query = self.db.query(Lead).filter(
            and_(
                Lead.initiator_id == initiator_id,
                Lead.recipient_id == recipient_id
            )
        )

        if project_id:
            query = query.filter(Lead.project_id == project_id)

        if listing_id:
            query = query.filter(Lead.listing_id == listing_id)

        return query.first()

    def find_by_user(
        self,
        user_id: int,
        as_initiator: bool = True
    ) -> List[Lead]:
        """
        Find all leads for a user (as initiator or recipient)

        Args:
            user_id: User ID
            as_initiator: True for leads initiated by user, False for leads received

        Returns:
            List of leads
        """
        query = self.db.query(Lead).options(
            joinedload(Lead.initiator),
            joinedload(Lead.recipient),
            joinedload(Lead.project)
        )

        if as_initiator:
            query = query.filter(Lead.initiator_id == user_id)
        else:
            query = query.filter(Lead.recipient_id == user_id)

        return query.order_by(Lead.created_at.desc()).all()

    def find_all_for_user(self, user_id: int) -> List[Lead]:
        """Find all leads where user is either initiator or recipient"""
        return self.db.query(Lead).options(
            joinedload(Lead.initiator),
            joinedload(Lead.recipient),
            joinedload(Lead.project)
        ).filter(
            or_(
                Lead.initiator_id == user_id,
                Lead.recipient_id == user_id
            )
        ).order_by(Lead.created_at.desc()).all()

    def update_status(self, lead_id: int, new_status: str) -> Optional[Lead]:
        """Update lead status"""
        lead = self.find_by_id(lead_id, include_relationships=False)

        if not lead:
            return None

        lead.status = new_status
        self.db.commit()
        self.db.refresh(lead)
        return lead

    # Message operations

    def create_message(self, message_data: dict) -> Message:
        """Create a new message"""
        message = Message(**message_data)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def find_messages_by_lead(self, lead_id: int) -> List[Message]:
        """Find all messages for a lead"""
        return self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(
            Message.lead_id == lead_id
        ).order_by(Message.sent_at.asc()).all()

    def count_messages_by_lead(self, lead_id: int) -> int:
        """Count messages in a lead conversation"""
        return self.db.query(Message).filter(
            Message.lead_id == lead_id
        ).count()
