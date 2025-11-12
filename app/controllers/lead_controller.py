"""
Lead Controller
Handles HTTP requests for lead endpoints
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.lead_service import LeadService
from app.dto.lead import (
    LeadCreateDTO,
    LeadResponseDTO,
    MessageCreateDTO,
    MessageResponseDTO,
    LeadListResponseDTO,
    MessageListResponseDTO
)
from app.middleware.auth import get_current_active_user
from app.models.user import User


router = APIRouter(prefix="/api/leads", tags=["Leads"])


@router.post(
    "",
    response_model=LeadResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create lead (first contact)",
    description="Create a lead when investor/buyer contacts developer/agency. Logs IP and timestamp for legal 'Proof of Introduction'."
)
def create_lead(
    data: LeadCreateDTO,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create lead (first contact)

    **Critical for Legal Compliance:**
    - Logs IP address of first contact
    - Records timestamp for 12-month tail period
    - Locks tier and fee rates at contact time
    - Prevents circumvention of platform fees

    **Requirements:**
    - Investor or buyer role only
    - Recipient must be developer or agency
    - Project must belong to recipient (if specified)

    **Duplicate Prevention:**
    - Cannot create multiple leads for same investor+developer+project combination

    **Tier/Fee Locking:**
    - Initiator tier locked at contact time
    - Recipient tier locked at contact time
    - Success fee rate locked based on recipient's tier

    **Success Fee Rates:**
    - Launch: 5%
    - Growth: 4%
    - Elite: 3%
    """
    service = LeadService(db)
    return service.create_lead(data, current_user, request)


@router.get(
    "/{lead_id}",
    response_model=LeadResponseDTO,
    summary="Get lead details",
    description="Get lead by ID. Only initiator or recipient can view."
)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get lead details

    **Access Control:**
    - Only initiator or recipient can view
    - Contains full contact information
    - Shows locked tier and fee rates

    **Use Cases:**
    - Review first contact details
    - Verify fee rate for deal tracking
    - Check 12-month tail period eligibility
    """
    service = LeadService(db)
    return service.get_lead(lead_id, current_user)


@router.get(
    "",
    response_model=LeadListResponseDTO,
    summary="List my leads",
    description="Get all leads for current user (as initiator or recipient)"
)
def list_my_leads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all leads for current user

    **Returns:**
    - Leads where user is initiator (contacted someone)
    - Leads where user is recipient (was contacted)
    - Sorted by most recent first

    **Use Cases:**
    - Investors: See all projects contacted
    - Developers: See all incoming inquiries
    - Track conversation history
    """
    service = LeadService(db)
    return service.list_my_leads(current_user)


@router.post(
    "/{lead_id}/messages",
    response_model=MessageResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Send message",
    description="Send message in lead conversation"
)
def send_message(
    lead_id: int,
    data: MessageCreateDTO,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send message in lead conversation

    **Access Control:**
    - Only initiator or recipient can send messages
    - Messages logged with IP address
    - Threaded to original lead

    **IP Logging:**
    - Each message logs sender IP
    - Provides audit trail for communications
    - Useful for dispute resolution

    **Use Cases:**
    - Investor asks questions about project
    - Developer provides additional information
    - Schedule meetings/calls
    - Negotiate terms
    """
    service = LeadService(db)
    return service.send_message(lead_id, current_user, data, request)


@router.get(
    "/{lead_id}/messages",
    response_model=MessageListResponseDTO,
    summary="Get conversation",
    description="Get all messages in lead conversation"
)
def get_messages(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all messages in lead conversation

    **Access Control:**
    - Only initiator or recipient can view messages
    - Messages returned in chronological order

    **Response:**
    - Full conversation history
    - Sender information for each message
    - Timestamps for all messages

    **Use Cases:**
    - Review conversation history
    - Verify what was discussed
    - Prepare for meetings
    - Legal documentation if needed
    """
    service = LeadService(db)
    return service.get_messages(lead_id, current_user)
