"""
Project Document Data Transfer Objects (DTOs)
Handles request/response validation for document endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class DocumentUploadDTO(BaseModel):
    """DTO for document metadata during upload"""
    doc_type: str = Field(..., description="Document type: IM, OM, pitch_deck, financial_model, legal, other")
    access_level: str = Field(default="public", description="Access level: public, verified_only, investor_only")
    description: Optional[str] = Field(None, max_length=500, description="Document description")

    @validator('doc_type')
    def validate_doc_type(cls, v):
        allowed = ['IM', 'OM', 'pitch_deck', 'financial_model', 'legal', 'brochure', 'floor_plans', 'photos', 'other']
        if v not in allowed:
            raise ValueError(f'doc_type must be one of: {", ".join(allowed)}')
        return v

    @validator('access_level')
    def validate_access_level(cls, v):
        allowed = ['public', 'verified_only', 'investor_only']
        if v not in allowed:
            raise ValueError(f'access_level must be one of: {", ".join(allowed)}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "doc_type": "IM",
                "access_level": "investor_only",
                "description": "Information Memorandum - Q4 2024"
            }
        }


class DocumentResponseDTO(BaseModel):
    """DTO for document response"""
    id: int
    project_id: int
    file_name: str
    file_url: str
    signed_url: Optional[str] = None  # Temporary signed URL for download
    signed_url_expires_at: Optional[datetime] = None
    doc_type: str
    access_level: str
    description: Optional[str] = None
    file_size: int
    checksum_sha256: str
    uploaded_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "project_id": 5,
                "file_name": "investment-memorandum.pdf",
                "file_url": "https://r2.example.com/bucket/documents/abc123.pdf",
                "signed_url": "https://r2.example.com/bucket/documents/abc123.pdf?X-Amz-Signature=...",
                "signed_url_expires_at": "2024-01-01T11:00:00",
                "doc_type": "IM",
                "access_level": "investor_only",
                "description": "Information Memorandum - Q4 2024",
                "file_size": 2048576,
                "checksum_sha256": "abc123def456...",
                "uploaded_at": "2024-01-01T10:00:00"
            }
        }


class DocumentListResponseDTO(BaseModel):
    """DTO for list of documents"""
    documents: list[DocumentResponseDTO]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "documents": [],
                "total": 5
            }
        }
