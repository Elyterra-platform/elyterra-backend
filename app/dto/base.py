"""
Base DTO/Schema classes
Using Pydantic for request/response validation
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    """Base DTO with common configuration"""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class BaseResponseDTO(BaseDTO):
    """Base response DTO with common fields"""

    id: int
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseDTO):
    """Pagination parameters"""

    page: int = 1
    limit: int = 10

    @property
    def skip(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseDTO):
    """Generic paginated response"""

    total: int
    page: int
    limit: int
    pages: int
    data: list
