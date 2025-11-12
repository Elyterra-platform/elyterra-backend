"""
Project Service
Handles business logic for project operations including quota enforcement
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from datetime import datetime
from app.repositories.project_repository import ProjectRepository
from app.models.user import User
from app.models.project import Project
from app.dto.project import (
    ProjectCreateDTO,
    ProjectUpdateDTO,
    ProjectResponseDTO,
    ProjectSearchDTO,
    ProjectListResponseDTO
)
from fastapi import HTTPException, status


class ProjectService:
    """Service for project business logic"""

    # Tier-based project quotas
    TIER_QUOTAS = {
        'launch': 3,
        'growth': 10,
        'elite': None  # Unlimited
    }

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProjectRepository(db)

    def create_project(self, developer: User, data: ProjectCreateDTO) -> ProjectResponseDTO:
        """
        Create a new project with quota and subscription validation
        """
        # Validate developer role
        if developer.role != 'developer':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only developers can create projects"
            )

        # Check subscription status
        if developer.subscription_status not in ['active', 'trial']:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Active subscription required to create projects"
            )

        # Check quota based on tier
        self._check_project_quota(developer)

        # Prepare project data (map DTO field names to database column names)
        project_data = {
            'developer_id': developer.id,
            'title': data.title,
            'description': data.description,
            'country': data.country,
            'city': data.city,
            'property_type': data.property_type,
            'total_investment_required': data.investment_required,  # Map to correct DB column
            'roi_estimate': data.roi_estimate,
            'status': 'draft',  # Always start as draft
            'access_level': data.access_level,
            'visibility_score': 0,  # Initial score
            'tags': data.tags or [],
        }

        # Create project
        project = self.repository.create(project_data)

        return self._to_response_dto(project)

    def get_project(self, project_id: int, user: Optional[User] = None) -> ProjectResponseDTO:
        """
        Get project by ID with access control
        """
        project = self.repository.find_by_id(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Check access permissions
        if not self._can_access_project(project, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this project"
            )

        return self._to_response_dto(project)

    def update_project(self, project_id: int, developer: User, data: ProjectUpdateDTO) -> ProjectResponseDTO:
        """
        Update project (owner only)
        """
        project = self.repository.find_by_id(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Check ownership
        if project.developer_id != developer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own projects"
            )

        # Prepare update data (exclude None values and map field names to DB columns)
        update_dict = data.model_dump(exclude_unset=True, exclude_none=True)

        # Map DTO field names to database column names
        update_data = {}
        for key, value in update_dict.items():
            if key == 'investment_required':
                update_data['total_investment_required'] = value
            elif key not in ['timeline_months', 'media_urls']:  # Skip fields not in DB
                update_data[key] = value

        # Update project
        updated_project = self.repository.update(project_id, update_data)

        return self._to_response_dto(updated_project)

    def delete_project(self, project_id: int, developer: User) -> dict:
        """
        Delete (archive) project (owner only)
        """
        project = self.repository.find_by_id(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Check ownership
        if project.developer_id != developer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own projects"
            )

        # Soft delete (archive)
        self.repository.delete(project_id)

        return {"message": "Project archived successfully"}

    def get_my_projects(self, developer: User) -> List[ProjectResponseDTO]:
        """
        Get all projects for the authenticated developer
        """
        projects = self.repository.find_by_developer(developer.id)

        return [self._to_response_dto(project) for project in projects]

    def search_projects(self, filters: ProjectSearchDTO, user: Optional[User] = None) -> ProjectListResponseDTO:
        """
        Search projects with tier-based visibility filtering
        """
        # Determine allowed access levels based on user tier
        access_levels = self._get_allowed_access_levels(user)

        # Perform search
        projects, total_count = self.repository.search(
            country=filters.country,
            city=filters.city,
            property_type=filters.property_type,
            min_investment=filters.min_investment,
            max_investment=filters.max_investment,
            min_roi=filters.min_roi,
            tags=filters.tags,
            status=filters.status,
            access_levels=access_levels,
            sort_by=filters.sort_by,
            sort_order=filters.sort_order,
            page=filters.page,
            page_size=filters.page_size
        )

        # Calculate total pages
        total_pages = (total_count + filters.page_size - 1) // filters.page_size

        return ProjectListResponseDTO(
            projects=[self._to_response_dto(project) for project in projects],
            total=total_count,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages
        )

    def publish_project(self, project_id: int, developer: User, new_status: str) -> ProjectResponseDTO:
        """
        Publish or unpublish a project
        """
        project = self.repository.find_by_id(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Check ownership
        if project.developer_id != developer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only publish your own projects"
            )

        # Check subscription status
        if developer.subscription_status not in ['active', 'trial']:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Active subscription required to publish projects"
            )

        # Update status
        updated_project = self.repository.update_status(project_id, new_status)

        return self._to_response_dto(updated_project)

    def increment_visibility(self, project_id: int, amount: int) -> ProjectResponseDTO:
        """
        Increment visibility score (for add-ons)
        """
        project = self.repository.increment_visibility_score(project_id, amount)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        return self._to_response_dto(project)

    # Private helper methods

    def _check_project_quota(self, developer: User):
        """Check if developer can create more projects based on tier quota"""
        tier = developer.tier.lower() if developer.tier else 'launch'
        quota = self.TIER_QUOTAS.get(tier, 3)  # Default to Launch tier

        # Elite tier has unlimited projects
        if quota is None:
            return

        # Count active projects (non-archived)
        current_count = self.repository.count_by_developer(developer.id)

        if current_count >= quota:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Project quota exceeded. Your {tier.capitalize()} tier allows {quota} projects. Upgrade to create more."
            )

    def _get_allowed_access_levels(self, user: Optional[User]) -> List[str]:
        """
        Determine which access levels the user can see based on their tier
        """
        # Anonymous users - public only
        if not user:
            return ['public']

        # Admin can see everything
        if user.role == 'admin':
            return ['public', 'verified_only', 'pre_launch', 'investor_only']

        # Developers can see their own + public
        if user.role == 'developer':
            return ['public', 'verified_only', 'pre_launch', 'investor_only']

        # Investors - tier-based access
        if user.role == 'investor':
            tier = user.tier.lower() if user.tier else 'explorer'

            if tier == 'explorer':
                return ['public']
            elif tier == 'insider':
                return ['public', 'verified_only']
            elif tier == 'capital partner':
                return ['public', 'verified_only', 'pre_launch', 'investor_only']

        # Default to public only
        return ['public']

    def _can_access_project(self, project: Project, user: Optional[User]) -> bool:
        """Check if user can access a specific project"""
        # Owner can always access
        if user and project.developer_id == user.id:
            return True

        # Admin can always access
        if user and user.role == 'admin':
            return True

        # Check if project's access level is in user's allowed levels
        allowed_levels = self._get_allowed_access_levels(user)
        return project.access_level in allowed_levels

    def _to_response_dto(self, project: Project) -> ProjectResponseDTO:
        """Convert Project model to ProjectResponseDTO"""
        # Get developer info if available
        developer_name = None
        developer_email = None

        if hasattr(project, 'developer') and project.developer:
            developer_name = project.developer.full_name
            # Mask email based on contact_visibility
            if project.contact_visibility == 'full':
                developer_email = project.developer.email
            elif project.contact_visibility == 'masked':
                developer_email = self._mask_email(project.developer.email)
            # else: none - don't show email

        return ProjectResponseDTO(
            id=project.id,
            developer_id=project.developer_id,
            developer_name=developer_name,
            developer_email=developer_email,
            title=project.title,
            description=project.description or "",
            country=project.country or "",
            city=project.city or "",
            property_type=project.property_type or "",
            investment_required=project.total_investment_required or 0,  # Map from DB column
            roi_estimate=project.roi_estimate,
            timeline_months=0,  # Not in DB, default to 0
            status=str(project.status.value) if hasattr(project.status, 'value') else str(project.status),
            access_level=str(project.access_level.value) if hasattr(project.access_level, 'value') else str(project.access_level),
            contact_visibility=str(project.contact_visibility.value) if hasattr(project.contact_visibility, 'value') else str(project.contact_visibility),
            visibility_score=int(project.visibility_score or 0),
            tags=project.tags or [],
            media_urls=[],  # Not in DB, return empty list
            created_at=project.created_at,
            updated_at=project.updated_at,
            published_at=getattr(project, 'published_at', None)
        )

    def _mask_email(self, email: str) -> str:
        """Mask email for privacy (e.g., j***@example.com)"""
        if not email or '@' not in email:
            return email

        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = local[0] + '***'
        else:
            masked_local = local[0] + '***' + local[-1]

        return f"{masked_local}@{domain}"
