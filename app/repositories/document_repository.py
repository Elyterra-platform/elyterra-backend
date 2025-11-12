"""
Document Repository
Handles database operations for project documents
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from app.models.project_document import ProjectDocument


class DocumentRepository:
    """Repository for document database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, document_data: dict) -> ProjectDocument:
        """Create a new document record"""
        document = ProjectDocument(**document_data)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def find_by_id(self, document_id: int) -> Optional[ProjectDocument]:
        """Find document by ID"""
        return self.db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

    def find_by_project(
        self,
        project_id: int,
        access_levels: Optional[List[str]] = None
    ) -> List[ProjectDocument]:
        """
        Find all documents for a project

        Args:
            project_id: Project ID
            access_levels: Filter by access levels (for tier-based filtering)

        Returns:
            List of documents
        """
        query = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        )

        if access_levels:
            query = query.filter(ProjectDocument.access_level.in_(access_levels))

        return query.order_by(ProjectDocument.uploaded_at.desc()).all()

    def update(self, document_id: int, update_data: dict) -> Optional[ProjectDocument]:
        """Update document metadata"""
        document = self.find_by_id(document_id)

        if not document:
            return None

        for key, value in update_data.items():
            if value is not None and hasattr(document, key):
                setattr(document, key, value)

        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, document_id: int) -> bool:
        """Delete document record"""
        document = self.find_by_id(document_id)

        if not document:
            return False

        self.db.delete(document)
        self.db.commit()
        return True

    def exists(self, document_id: int) -> bool:
        """Check if document exists"""
        return self.db.query(ProjectDocument.id).filter(
            ProjectDocument.id == document_id
        ).first() is not None

    def count_by_project(self, project_id: int) -> int:
        """Count documents for a project"""
        return self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).count()

    def find_by_checksum(self, checksum: str) -> Optional[ProjectDocument]:
        """Find document by SHA-256 checksum (for duplicate detection)"""
        return self.db.query(ProjectDocument).filter(
            ProjectDocument.checksum_sha256 == checksum
        ).first()
