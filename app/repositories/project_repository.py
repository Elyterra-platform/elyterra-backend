"""
Project Repository
Handles database operations for projects
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Tuple
from app.models.project import Project, ProjectStatus
from app.models.user import User
from decimal import Decimal


class ProjectRepository:
    """Repository for project database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, project_data: dict) -> Project:
        """Create a new project"""
        project = Project(**project_data)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        # Load developer relationship for response DTO
        self.db.refresh(project, ['developer'])
        return project

    def find_by_id(self, project_id: int, include_developer: bool = True) -> Optional[Project]:
        """Find project by ID with optional developer relationship"""
        query = self.db.query(Project)

        if include_developer:
            query = query.options(joinedload(Project.developer))

        return query.filter(Project.id == project_id).first()

    def find_by_developer(self, developer_id: int, status: Optional[str] = None) -> List[Project]:
        """Find all projects by developer ID"""
        query = self.db.query(Project).filter(Project.developer_id == developer_id)

        if status:
            query = query.filter(Project.status == status)

        return query.order_by(desc(Project.created_at)).all()

    def count_by_developer(self, developer_id: int, status: Optional[str] = None) -> int:
        """Count projects by developer (for quota enforcement)"""
        query = self.db.query(func.count(Project.id)).filter(
            Project.developer_id == developer_id
        )

        if status:
            query = query.filter(Project.status == status)
        else:
            # Count non-archived projects by default
            query = query.filter(Project.status != "archived")

        return query.scalar()

    def update(self, project_id: int, update_data: dict) -> Optional[Project]:
        """Update project by ID"""
        project = self.find_by_id(project_id, include_developer=False)

        if not project:
            return None

        for key, value in update_data.items():
            if value is not None and hasattr(project, key):
                setattr(project, key, value)

        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project_id: int) -> bool:
        """Soft delete project (set status to archived)"""
        project = self.find_by_id(project_id, include_developer=False)

        if not project:
            return False

        project.status = "archived"
        self.db.commit()
        return True

    def search(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        property_type: Optional[str] = None,
        min_investment: Optional[Decimal] = None,
        max_investment: Optional[Decimal] = None,
        min_roi: Optional[Decimal] = None,
        tags: Optional[List[str]] = None,
        status: str = "published",
        access_levels: Optional[List[str]] = None,
        sort_by: str = "visibility_score",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Project], int]:
        """
        Search projects with filters and pagination
        Returns (projects, total_count)
        """
        # Base query with developer relationship
        query = self.db.query(Project).options(joinedload(Project.developer))

        # Apply filters
        filters = []

        if status:
            filters.append(Project.status == status)

        if country:
            filters.append(Project.country.ilike(f"%{country}%"))

        if city:
            filters.append(Project.city.ilike(f"%{city}%"))

        if property_type:
            filters.append(Project.property_type == property_type)

        if min_investment is not None:
            filters.append(Project.total_investment_required >= min_investment)

        if max_investment is not None:
            filters.append(Project.total_investment_required <= max_investment)

        if min_roi is not None:
            filters.append(Project.roi_estimate >= min_roi)

        # JSONB tag search (PostgreSQL specific)
        if tags and len(tags) > 0:
            # Check if any of the provided tags exist in the project's tags array
            tag_filters = []
            for tag in tags:
                tag_filters.append(Project.tags.contains([tag]))
            filters.append(or_(*tag_filters))

        # Access level filtering (tier-based)
        if access_levels and len(access_levels) > 0:
            filters.append(Project.access_level.in_(access_levels))

        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))

        # Get total count before pagination
        total_count = query.count()

        # Apply sorting (map DTO field names to DB column names)
        sort_field = 'total_investment_required' if sort_by == 'investment_required' else sort_by
        sort_column = getattr(Project, sort_field, Project.visibility_score)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        projects = query.all()

        return projects, total_count

    def increment_visibility_score(self, project_id: int, amount: int) -> Optional[Project]:
        """Increment visibility score (used for add-ons)"""
        project = self.find_by_id(project_id, include_developer=False)

        if not project:
            return None

        project.visibility_score += amount
        self.db.commit()
        self.db.refresh(project)
        return project

    def update_status(self, project_id: int, new_status: str) -> Optional[Project]:
        """Update project status"""
        project = self.find_by_id(project_id, include_developer=False)

        if not project:
            return None

        project.status = new_status

        # Set published_at timestamp when publishing
        if new_status == 'published' and not project.published_at:
            from datetime import datetime
            project.published_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(project)
        return project

    def exists(self, project_id: int) -> bool:
        """Check if project exists"""
        return self.db.query(Project.id).filter(Project.id == project_id).first() is not None

    def get_developer_projects_count_by_status(self, developer_id: int) -> dict:
        """Get count of projects by status for a developer"""
        from sqlalchemy import case

        result = self.db.query(
            Project.status,
            func.count(Project.id).label('count')
        ).filter(
            Project.developer_id == developer_id
        ).group_by(Project.status).all()

        return {row.status: row.count for row in result}
