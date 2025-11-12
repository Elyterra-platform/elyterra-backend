"""
Project Controller
Handles HTTP requests for project endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.services.project_service import ProjectService
from app.dto.project import (
    ProjectCreateDTO,
    ProjectUpdateDTO,
    ProjectResponseDTO,
    ProjectSearchDTO,
    ProjectListResponseDTO,
    ProjectPublishDTO
)
from app.middleware.auth import get_current_user, get_current_active_user, require_role
from app.models.user import User


router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new investment project. Requires developer role and active subscription. Subject to tier-based quota limits."
)
def create_project(
    data: ProjectCreateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("developer"))
):
    """
    Create a new investment project

    **Requirements:**
    - Developer role
    - Active subscription
    - Within tier quota limits (Launch: 3, Growth: 10, Elite: unlimited)

    **Project starts as 'draft' status**
    """
    service = ProjectService(db)
    return service.create_project(current_user, data)


@router.get(
    "/{project_id}",
    response_model=ProjectResponseDTO,
    summary="Get project by ID",
    description="Get a single project by ID. Access control based on user tier and project access_level."
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get a single project by ID

    **Access Control:**
    - Public projects: All users (including anonymous)
    - Verified_only: Insider tier and above
    - Pre_launch/Investor_only: Capital Partner tier only
    - Owners and admins: Full access to their projects
    """
    service = ProjectService(db)
    return service.get_project(project_id, current_user)


@router.get(
    "",
    response_model=ProjectListResponseDTO,
    summary="Search and list projects",
    description="Search projects with filters. Results automatically filtered based on user tier."
)
def search_projects(
    country: Optional[str] = Query(None, description="Filter by country"),
    city: Optional[str] = Query(None, description="Filter by city"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    min_investment: Optional[float] = Query(None, description="Minimum investment amount"),
    max_investment: Optional[float] = Query(None, description="Maximum investment amount"),
    min_roi: Optional[float] = Query(None, description="Minimum ROI estimate"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    status: str = Query("published", description="Filter by status"),
    sort_by: str = Query("visibility_score", description="Sort field: visibility_score, created_at, investment_required, roi_estimate"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Search and filter projects

    **Automatic Tier-Based Filtering:**
    - Anonymous/Explorer: Public projects only
    - Insider: Public + Verified_only projects
    - Capital Partner: All projects including pre_launch
    - Developers: Own projects + public projects
    - Admin: All projects

    **Sorting Options:**
    - visibility_score: Featured/boosted projects first
    - created_at: Newest first
    - investment_required: By investment size
    - roi_estimate: By expected ROI
    """
    # Parse tags if provided
    tag_list = tags.split(',') if tags else None

    # Build search filters
    filters = ProjectSearchDTO(
        country=country,
        city=city,
        property_type=property_type,
        min_investment=min_investment,
        max_investment=max_investment,
        min_roi=min_roi,
        tags=tag_list,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )

    service = ProjectService(db)
    return service.search_projects(filters, current_user)


@router.put(
    "/{project_id}",
    response_model=ProjectResponseDTO,
    summary="Update project",
    description="Update an existing project. Only the project owner can update."
)
def update_project(
    project_id: int,
    data: ProjectUpdateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("developer"))
):
    """
    Update an existing project

    **Authorization:** Only the project owner can update
    **Partial Updates:** Only provided fields will be updated
    """
    service = ProjectService(db)
    return service.update_project(project_id, current_user, data)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete (archive) project",
    description="Soft delete a project by setting status to 'archived'. Only the project owner can delete."
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("developer"))
):
    """
    Delete (archive) a project

    **Authorization:** Only the project owner can delete
    **Note:** This is a soft delete - project is archived, not removed from database
    """
    service = ProjectService(db)
    return service.delete_project(project_id, current_user)


@router.get(
    "/my/projects",
    response_model=List[ProjectResponseDTO],
    summary="Get my projects",
    description="Get all projects created by the authenticated developer"
)
def get_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("developer"))
):
    """
    Get all projects for the authenticated developer

    **Returns:** All projects (draft, published, archived) owned by the developer
    **Sorted by:** Most recent first
    """
    service = ProjectService(db)
    return service.get_my_projects(current_user)


@router.patch(
    "/{project_id}/publish",
    response_model=ProjectResponseDTO,
    summary="Publish or unpublish project",
    description="Change project status between 'draft' and 'published'"
)
def publish_project(
    project_id: int,
    data: ProjectPublishDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("developer"))
):
    """
    Publish or unpublish a project

    **Authorization:** Only the project owner can publish
    **Requirements:** Active subscription

    **Status Transitions:**
    - draft → published: Makes project visible to investors
    - published → draft: Hides project from search

    **Note:** Sets published_at timestamp when first published
    """
    service = ProjectService(db)
    return service.publish_project(project_id, current_user, data.status)


# Admin endpoint for visibility boost (for add-ons feature in Milestone 4)
@router.patch(
    "/{project_id}/visibility",
    response_model=ProjectResponseDTO,
    summary="Increment visibility score",
    description="Increment project visibility score (Admin only, used for add-ons)"
)
def increment_visibility(
    project_id: int,
    amount: int = Query(..., ge=1, le=1000, description="Amount to increment"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Increment project visibility score

    **Authorization:** Admin only
    **Use Case:** Applied when developer purchases visibility boost add-on
    **Effect:** Higher visibility_score ranks project higher in search results
    """
    service = ProjectService(db)
    return service.increment_visibility(project_id, amount)
