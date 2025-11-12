"""
Lead Data Transfer Objects (DTOs)
Handles request/response validation for lead endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LeadCreateDTO(BaseModel):
    """DTO for creating a lead (first contact)"""
    recipient_id: int = Field(..., description="Developer/agency user ID being contacted")
    project_id: Optional[int] = Field(None, description="Project ID (if contacting about specific project)")
    listing_id: Optional[int] = Field(None, description="Listing ID (for agency listings)")
    message: Optional[str] = Field(None, max_length=1000, description="Initial message")

    class Config:
        json_schema_extra = {
            "example": {
                "recipient_id": 5,
                "project_id": 10,
                "message": "I'm interested in learning more about this investment opportunity."
            }
        }


class LeadResponseDTO(BaseModel):
    """DTO for lead response"""
    id: int
    initiator_id: int
    initiator_name: Optional[str] = None
    initiator_email: Optional[str] = None
    recipient_id: int
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    project_id: Optional[int] = None
    project_title: Optional[str] = None
    listing_id: Optional[int] = None
    status: str
    origin: str
    first_contact_ip: str
    first_contact_user_agent: Optional[str] = None
    initiator_tier_locked: str
    recipient_tier_locked: str
    success_fee_rate_locked: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "initiator_id": 15,
                "initiator_name": "John Investor",
                "initiator_email": "john@example.com",
                "recipient_id": 5,
                "recipient_name": "Developer Company",
                "recipient_email": "dev@example.com",
                "project_id": 10,
                "project_title": "Luxury Development - Lisbon",
                "listing_id": None,
                "status": "active",
                "origin": "platform",
                "first_contact_ip": "192.168.1.1",
                "first_contact_user_agent": "Mozilla/5.0...",
                "initiator_tier_locked": "insider",
                "recipient_tier_locked": "growth",
                "success_fee_rate_locked": 3.0,
                "created_at": "2024-01-01T10:00:00"
            }
        }


class MessageCreateDTO(BaseModel):
    """DTO for sending a message in a lead conversation"""
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Thank you for your interest. I'd be happy to schedule a call to discuss the project details."
            }
        }


class MessageResponseDTO(BaseModel):
    """DTO for message response"""
    id: int
    lead_id: int
    sender_id: int
    sender_name: Optional[str] = None
    content: str
    sent_at: datetime
    sent_from_ip: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "lead_id": 1,
                "sender_id": 5,
                "sender_name": "Developer Company",
                "content": "Thank you for your interest...",
                "sent_at": "2024-01-01T10:05:00",
                "sent_from_ip": "192.168.1.2"
            }
        }


class LeadListResponseDTO(BaseModel):
    """DTO for paginated lead list"""
    leads: list[LeadResponseDTO]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "leads": [],
                "total": 10
            }
        }


class MessageListResponseDTO(BaseModel):
    """DTO for message conversation"""
    messages: list[MessageResponseDTO]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [],
                "total": 5
            }
        }
