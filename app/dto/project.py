"""
Project Data Transfer Objects (DTOs)
Handles request/response validation for project endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class ProjectCreateDTO(BaseModel):
    """DTO for creating a new project"""
    title: str = Field(..., min_length=3, max_length=200, description="Project title")
    description: str = Field(..., min_length=10, max_length=5000, description="Project description")
    country: str = Field(..., min_length=2, max_length=100, description="Project country")
    city: str = Field(..., min_length=2, max_length=100, description="Project city")
    property_type: str = Field(..., description="Type of property (e.g., residential, commercial)")
    investment_required: Decimal = Field(..., gt=0, description="Total investment amount required")
    roi_estimate: Optional[Decimal] = Field(None, ge=0, le=100, description="Expected ROI percentage")
    timeline_months: Optional[int] = Field(None, gt=0, le=360, description="Project timeline in months")
    access_level: str = Field(default="public", description="Access level: public, verified_only, pre_launch, investor_only")
    contact_visibility: str = Field(default="full", description="Contact visibility: full, masked, none")
    tags: Optional[List[str]] = Field(default=[], description="Project tags for search")
    media_urls: Optional[List[str]] = Field(default=[], description="URLs to project images/videos")

    @validator('access_level')
    def validate_access_level(cls, v):
        allowed = ['public', 'verified_only', 'pre_launch', 'investor_only']
        if v not in allowed:
            raise ValueError(f'access_level must be one of: {", ".join(allowed)}')
        return v

    @validator('contact_visibility')
    def validate_contact_visibility(cls, v):
        allowed = ['full', 'masked', 'none']
        if v not in allowed:
            raise ValueError(f'contact_visibility must be one of: {", ".join(allowed)}')
        return v

    @validator('tags')
    def validate_tags(cls, v):
        if v and len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Luxury Residential Development - Lisbon",
                "description": "Premium residential project in central Lisbon with 50 units",
                "country": "Portugal",
                "city": "Lisbon",
                "property_type": "residential",
                "investment_required": 5000000.00,
                "roi_estimate": 18.5,
                "timeline_months": 24,
                "access_level": "public",
                "contact_visibility": "full",
                "tags": ["luxury", "residential", "lisbon", "high-roi"],
                "media_urls": ["https://example.com/image1.jpg"]
            }
        }


class ProjectUpdateDTO(BaseModel):
    """DTO for updating an existing project (all fields optional)"""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    property_type: Optional[str] = None
    investment_required: Optional[Decimal] = Field(None, gt=0)
    roi_estimate: Optional[Decimal] = Field(None, ge=0, le=100)
    timeline_months: Optional[int] = Field(None, gt=0, le=360)
    access_level: Optional[str] = None
    contact_visibility: Optional[str] = None
    tags: Optional[List[str]] = None
    media_urls: Optional[List[str]] = None

    @validator('access_level')
    def validate_access_level(cls, v):
        if v is not None:
            allowed = ['public', 'verified_only', 'pre_launch', 'investor_only']
            if v not in allowed:
                raise ValueError(f'access_level must be one of: {", ".join(allowed)}')
        return v

    @validator('contact_visibility')
    def validate_contact_visibility(cls, v):
        if v is not None:
            allowed = ['full', 'masked', 'none']
            if v not in allowed:
                raise ValueError(f'contact_visibility must be one of: {", ".join(allowed)}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Project Title",
                "roi_estimate": 20.0,
                "access_level": "verified_only"
            }
        }


class ProjectResponseDTO(BaseModel):
    """DTO for project response"""
    id: int
    developer_id: int
    developer_name: Optional[str] = None
    developer_email: Optional[str] = None
    title: str
    description: str
    country: str
    city: str
    property_type: str
    investment_required: Decimal
    roi_estimate: Optional[Decimal] = None
    timeline_months: Optional[int] = None
    status: str
    access_level: str
    contact_visibility: str
    visibility_score: int
    tags: List[str]
    media_urls: List[str]
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "developer_id": 5,
                "developer_name": "John Developer",
                "developer_email": "john@example.com",
                "title": "Luxury Residential Development - Lisbon",
                "description": "Premium residential project in central Lisbon",
                "country": "Portugal",
                "city": "Lisbon",
                "property_type": "residential",
                "investment_required": 5000000.00,
                "roi_estimate": 18.5,
                "timeline_months": 24,
                "status": "published",
                "access_level": "public",
                "contact_visibility": "full",
                "visibility_score": 100,
                "tags": ["luxury", "residential", "lisbon"],
                "media_urls": ["https://example.com/image1.jpg"],
                "created_at": "2024-01-01T10:00:00",
                "updated_at": "2024-01-01T10:00:00",
                "published_at": "2024-01-01T10:00:00"
            }
        }


class ProjectSearchDTO(BaseModel):
    """DTO for searching/filtering projects"""
    country: Optional[str] = None
    city: Optional[str] = None
    property_type: Optional[str] = None
    min_investment: Optional[Decimal] = Field(None, ge=0)
    max_investment: Optional[Decimal] = Field(None, ge=0)
    min_roi: Optional[Decimal] = Field(None, ge=0)
    tags: Optional[List[str]] = None
    status: str = Field(default="published", description="Filter by status")
    access_level: Optional[str] = None  # Admin override only

    # Sorting
    sort_by: str = Field(default="visibility_score", description="Sort field: visibility_score, created_at, investment_required")
    sort_order: str = Field(default="desc", description="Sort order: asc or desc")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed = ['visibility_score', 'created_at', 'investment_required', 'roi_estimate']
        if v not in allowed:
            raise ValueError(f'sort_by must be one of: {", ".join(allowed)}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v

    @validator('max_investment')
    def validate_investment_range(cls, v, values):
        if v is not None and 'min_investment' in values and values['min_investment'] is not None:
            if v < values['min_investment']:
                raise ValueError('max_investment must be greater than min_investment')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "country": "Portugal",
                "city": "Lisbon",
                "min_investment": 1000000,
                "max_investment": 10000000,
                "min_roi": 15.0,
                "tags": ["luxury", "residential"],
                "sort_by": "visibility_score",
                "sort_order": "desc",
                "page": 1,
                "page_size": 20
            }
        }


class ProjectListResponseDTO(BaseModel):
    """DTO for paginated project list response"""
    projects: List[ProjectResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "projects": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }


class ProjectPublishDTO(BaseModel):
    """DTO for publishing a project"""
    status: str = Field(..., description="New status: published or draft")

    @validator('status')
    def validate_status(cls, v):
        if v not in ['published', 'draft']:
            raise ValueError('status must be "published" or "draft"')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "status": "published"
            }
        }
