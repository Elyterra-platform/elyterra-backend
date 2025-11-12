"""
Lead Service
Handles business logic for lead operations including IP logging and tier locking
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status, Request

from app.repositories.lead_repository import LeadRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.models.lead import Lead, Message
from app.dto.lead import (
    LeadCreateDTO,
    LeadResponseDTO,
    MessageCreateDTO,
    MessageResponseDTO,
    LeadListResponseDTO,
    MessageListResponseDTO
)
from app.utils.request import get_client_ip, get_user_agent


class LeadService:
    """Service for lead business logic"""

    # Success fee rates by tier (for future deal tracking)
    TIER_FEE_RATES = {
        'launch': 5.0,      # 5%
        'growth': 4.0,      # 4%
        'elite': 3.0,       # 3%
        'explorer': 0.0,    # Investors don't pay fees
        'insider': 0.0,
        'capital partner': 0.0
    }

    def __init__(self, db: Session):
        self.db = db
        self.repository = LeadRepository(db)
        self.project_repository = ProjectRepository(db)
        self.user_repository = UserRepository(db)

    def create_lead(
        self,
        data: LeadCreateDTO,
        initiator: User,
        request: Request
    ) -> LeadResponseDTO:
        """
        Create a new lead (first contact)

        This is critical for legal "Proof of Introduction" for the 12-month tail period.
        Captures IP address, timestamp, and tier/fee rates at time of first contact.

        Args:
            data: Lead creation data
            initiator: User initiating contact (investor/buyer)
            request: HTTP request for IP logging

        Returns:
            LeadResponseDTO

        Raises:
            HTTPException: If validation fails or duplicate lead
        """
        # Validate initiator role (must be investor or buyer)
        if initiator.role not in ['investor', 'buyer']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only investors and buyers can initiate leads"
            )

        # Validate recipient exists
        recipient = self.user_repository.find_by_id(data.recipient_id)

        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient user not found"
            )

        # Validate recipient role (must be developer or agency)
        if recipient.role not in ['developer', 'agency']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only contact developers or agencies"
            )

        # Validate project if provided
        if data.project_id:
            project = self.project_repository.find_by_id(data.project_id)

            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )

            # Verify project belongs to recipient
            if project.developer_id != recipient.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Project does not belong to recipient"
                )

        # Check for existing lead (prevent duplicates)
        existing_lead = self.repository.find_existing_lead(
            initiator.id,
            recipient.id,
            data.project_id,
            data.listing_id
        )

        if existing_lead:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lead already exists between these users for this project/listing"
            )

        # Extract IP and User-Agent for legal logging
        client_ip = get_client_ip(request)
        user_agent = get_user_agent(request)

        if not client_ip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to determine client IP address"
            )

        # Lock tier and fee rates at time of contact
        initiator_tier = initiator.tier or 'explorer'
        recipient_tier = recipient.tier or 'launch'

        success_fee_rate = self.TIER_FEE_RATES.get(
            recipient_tier.lower(),
            5.0  # Default 5%
        )

        # Create lead record
        lead_data = {
            'initiator_id': initiator.id,
            'recipient_id': recipient.id,
            'project_id': data.project_id,
            'listing_id': data.listing_id,
            'status': 'active',
            'origin': 'platform',
            'first_contact_ip': client_ip,
            'first_contact_user_agent': user_agent,
            'initiator_tier_locked': initiator_tier,
            'recipient_tier_locked': recipient_tier,
            'success_fee_rate_locked': success_fee_rate
        }

        lead = self.repository.create(lead_data)

        # Send initial message if provided
        if data.message:
            self._create_message_internal(
                lead.id,
                initiator.id,
                data.message,
                client_ip
            )

        return self._to_response_dto(lead)

    def get_lead(self, lead_id: int, user: User) -> LeadResponseDTO:
        """
        Get lead by ID (with access control)

        Args:
            lead_id: Lead ID
            user: Current user

        Returns:
            LeadResponseDTO

        Raises:
            HTTPException: If not found or access denied
        """
        lead = self.repository.find_by_id(lead_id)

        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )

        # Check access (must be initiator or recipient)
        if lead.initiator_id != user.id and lead.recipient_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this lead"
            )

        return self._to_response_dto(lead)

    def list_my_leads(self, user: User) -> LeadListResponseDTO:
        """
        List all leads for current user (as initiator or recipient)

        Args:
            user: Current user

        Returns:
            LeadListResponseDTO
        """
        leads = self.repository.find_all_for_user(user.id)

        return LeadListResponseDTO(
            leads=[self._to_response_dto(lead) for lead in leads],
            total=len(leads)
        )

    def send_message(
        self,
        lead_id: int,
        sender: User,
        data: MessageCreateDTO,
        request: Request
    ) -> MessageResponseDTO:
        """
        Send message in lead conversation

        Args:
            lead_id: Lead ID
            sender: User sending message
            data: Message content
            request: HTTP request for IP logging

        Returns:
            MessageResponseDTO

        Raises:
            HTTPException: If lead not found or access denied
        """
        lead = self.repository.find_by_id(lead_id)

        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )

        # Check access (must be initiator or recipient)
        if lead.initiator_id != sender.id and lead.recipient_id != sender.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to send messages in this lead"
            )

        # Extract IP for logging
        client_ip = get_client_ip(request)

        message = self._create_message_internal(
            lead_id,
            sender.id,
            data.content,
            client_ip
        )

        return self._to_message_dto(message)

    def get_messages(self, lead_id: int, user: User) -> MessageListResponseDTO:
        """
        Get all messages in lead conversation

        Args:
            lead_id: Lead ID
            user: Current user

        Returns:
            MessageListResponseDTO

        Raises:
            HTTPException: If lead not found or access denied
        """
        lead = self.repository.find_by_id(lead_id)

        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )

        # Check access
        if lead.initiator_id != user.id and lead.recipient_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view messages in this lead"
            )

        messages = self.repository.find_messages_by_lead(lead_id)

        return MessageListResponseDTO(
            messages=[self._to_message_dto(msg) for msg in messages],
            total=len(messages)
        )

    # Private helper methods

    def _create_message_internal(
        self,
        lead_id: int,
        sender_id: int,
        content: str,
        ip_address: Optional[str]
    ) -> Message:
        """Internal method to create message"""
        message_data = {
            'lead_id': lead_id,
            'sender_id': sender_id,
            'content': content,
            'sent_from_ip': ip_address
        }

        return self.repository.create_message(message_data)

    def _to_response_dto(self, lead: Lead) -> LeadResponseDTO:
        """Convert Lead model to LeadResponseDTO"""
        initiator_name = None
        initiator_email = None
        recipient_name = None
        recipient_email = None
        project_title = None

        # Get user info if relationships loaded
        if hasattr(lead, 'initiator') and lead.initiator:
            initiator_name = lead.initiator.full_name
            initiator_email = lead.initiator.email

        if hasattr(lead, 'recipient') and lead.recipient:
            recipient_name = lead.recipient.full_name
            recipient_email = lead.recipient.email

        if hasattr(lead, 'project') and lead.project:
            project_title = lead.project.title

        return LeadResponseDTO(
            id=lead.id,
            initiator_id=lead.initiator_id,
            initiator_name=initiator_name,
            initiator_email=initiator_email,
            recipient_id=lead.recipient_id,
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            project_id=lead.project_id,
            project_title=project_title,
            listing_id=lead.listing_id,
            status=lead.status,
            origin=lead.origin,
            first_contact_ip=lead.first_contact_ip,
            first_contact_user_agent=lead.first_contact_user_agent,
            initiator_tier_locked=lead.initiator_tier_locked,
            recipient_tier_locked=lead.recipient_tier_locked,
            success_fee_rate_locked=lead.success_fee_rate_locked,
            created_at=lead.created_at
        )

    def _to_message_dto(self, message: Message) -> MessageResponseDTO:
        """Convert Message model to MessageResponseDTO"""
        sender_name = None

        if hasattr(message, 'sender') and message.sender:
            sender_name = message.sender.full_name

        return MessageResponseDTO(
            id=message.id,
            lead_id=message.lead_id,
            sender_id=message.sender_id,
            sender_name=sender_name,
            content=message.content,
            sent_at=message.sent_at,
            sent_from_ip=message.sent_from_ip
        )
