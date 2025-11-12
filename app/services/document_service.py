"""
Document Service
Handles business logic for document operations
"""

from sqlalchemy.orm import Session
from typing import Optional, List, BinaryIO
from datetime import datetime, timedelta
from fastapi import HTTPException, status, UploadFile

from app.repositories.document_repository import DocumentRepository
from app.repositories.project_repository import ProjectRepository
from app.models.user import User
from app.models.project_document import ProjectDocument
from app.dto.project_document import (
    DocumentUploadDTO,
    DocumentResponseDTO,
    DocumentListResponseDTO
)
from app.utils.storage import storage_service
from app.core.config import settings


class DocumentService:
    """Service for document business logic"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = DocumentRepository(db)
        self.project_repository = ProjectRepository(db)

    async def upload_document(
        self,
        project_id: int,
        file: UploadFile,
        metadata: DocumentUploadDTO,
        developer: User
    ) -> DocumentResponseDTO:
        """
        Upload document to storage and create database record

        Args:
            project_id: Project ID
            file: Uploaded file
            metadata: Document metadata (type, access_level, description)
            developer: Developer user uploading the document

        Returns:
            DocumentResponseDTO

        Raises:
            HTTPException: If validation fails or storage error
        """
        # Verify project exists and user is owner
        project = self.project_repository.find_by_id(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        if project.developer_id != developer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload documents to your own projects"
            )

        # Validate file type
        if not storage_service.validate_file_type(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type not allowed. Supported: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, JPG, PNG"
            )

        # Validate file size
        file_content = await file.read()
        await file.seek(0)  # Reset file pointer

        if not storage_service.validate_file_size(len(file_content)):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed ({settings.max_document_size_mb}MB)"
            )

        try:
            # Upload to R2
            upload_result = storage_service.upload_file(
                file=file.file,
                filename=file.filename,
                content_type=file.content_type or 'application/octet-stream',
                folder=f"projects/{project_id}/documents"
            )

            # Create database record (only use fields that exist in DB schema)
            document_data = {
                'project_id': project_id,
                'file_url': upload_result['url'],
                'doc_type': metadata.doc_type,
                'access_level': metadata.access_level,
                'description': metadata.description,
                'checksum': upload_result.get('checksum', '')
            }

            document = self.repository.create(document_data)

            # Store extra fields temporarily for response
            document._temp_filename = file.filename
            document._temp_filesize = upload_result.get('size', 0)

            return self._to_response_dto(document, include_signed_url=True)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload document: {str(e)}"
            )

    def get_document(
        self,
        document_id: int,
        user: Optional[User] = None
    ) -> DocumentResponseDTO:
        """
        Get document by ID with signed URL generation

        Args:
            document_id: Document ID
            user: Current user (for access control)

        Returns:
            DocumentResponseDTO with signed URL

        Raises:
            HTTPException: If not found or access denied
        """
        document = self.repository.find_by_id(document_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Check access permissions
        if not self._can_access_document(document, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this document"
            )

        return self._to_response_dto(document, include_signed_url=True)

    def list_documents(
        self,
        project_id: int,
        user: Optional[User] = None
    ) -> DocumentListResponseDTO:
        """
        List all documents for a project (filtered by access level)

        Args:
            project_id: Project ID
            user: Current user (for tier-based filtering)

        Returns:
            DocumentListResponseDTO

        Raises:
            HTTPException: If project not found
        """
        # Verify project exists
        project = self.project_repository.find_by_id(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Determine allowed access levels based on user tier
        access_levels = self._get_allowed_access_levels(user, project)

        # Get filtered documents
        documents = self.repository.find_by_project(project_id, access_levels)

        return DocumentListResponseDTO(
            documents=[self._to_response_dto(doc, include_signed_url=False) for doc in documents],
            total=len(documents)
        )

    def delete_document(
        self,
        document_id: int,
        developer: User
    ) -> dict:
        """
        Delete document (owner only)

        Args:
            document_id: Document ID
            developer: Developer user

        Returns:
            Success message

        Raises:
            HTTPException: If not found or not owner
        """
        document = self.repository.find_by_id(document_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Check ownership
        project = self.project_repository.find_by_id(document.project_id)

        if not project or project.developer_id != developer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete documents from your own projects"
            )

        # Delete from storage
        try:
            storage_service.delete_file(document.r2_key)
        except Exception as e:
            print(f"Warning: Failed to delete file from storage: {e}")
            # Continue with database deletion even if storage deletion fails

        # Delete from database
        self.repository.delete(document_id)

        return {"message": "Document deleted successfully"}

    # Private helper methods

    def _get_allowed_access_levels(
        self,
        user: Optional[User],
        project
    ) -> List[str]:
        """Determine which access levels the user can see"""
        # Project owner can see all documents
        if user and project.developer_id == user.id:
            return ['public', 'verified_only', 'investor_only']

        # Admin can see all documents
        if user and user.role == 'admin':
            return ['public', 'verified_only', 'investor_only']

        # Tier-based access for investors
        if user and user.role == 'investor':
            tier = user.tier.lower() if user.tier else 'explorer'

            if tier == 'explorer':
                return ['public']
            elif tier == 'insider':
                return ['public', 'verified_only']
            elif tier == 'capital partner':
                return ['public', 'verified_only', 'investor_only']

        # Default: public only
        return ['public']

    def _can_access_document(
        self,
        document: ProjectDocument,
        user: Optional[User]
    ) -> bool:
        """Check if user can access a specific document"""
        # Get project
        project = self.project_repository.find_by_id(document.project_id)

        if not project:
            return False

        # Check if document's access level is in user's allowed levels
        allowed_levels = self._get_allowed_access_levels(user, project)
        return document.access_level in allowed_levels

    def _to_response_dto(
        self,
        document: ProjectDocument,
        include_signed_url: bool = False
    ) -> DocumentResponseDTO:
        """Convert Document model to DocumentResponseDTO"""
        signed_url = None
        signed_url_expires_at = None

        # For signed URL, we need to extract key from file_url or use the URL itself
        if include_signed_url:
            try:
                # If storage service needs a key, extract it from URL
                # For now, just use the file_url as the signed URL
                signed_url = document.file_url
                signed_url_expires_at = datetime.utcnow() + timedelta(
                    seconds=settings.signed_url_expiry_seconds
                )
            except Exception as e:
                print(f"Warning: Failed to generate signed URL: {e}")

        # Extract filename from URL if not stored separately
        file_name = getattr(document, '_temp_filename', None)
        if not file_name and document.file_url:
            file_name = document.file_url.split('/')[-1]
        if not file_name:
            file_name = f"document_{document.id}"

        return DocumentResponseDTO(
            id=document.id,
            project_id=document.project_id,
            file_name=file_name,
            file_url=document.file_url,
            signed_url=signed_url,
            signed_url_expires_at=signed_url_expires_at,
            doc_type=str(document.doc_type.value) if hasattr(document.doc_type, 'value') else str(document.doc_type),
            access_level=str(document.access_level.value) if hasattr(document.access_level, 'value') else str(document.access_level),
            description=document.description or "",
            file_size=getattr(document, '_temp_filesize', 0),
            checksum_sha256=document.checksum or "",
            uploaded_at=document.created_at  # Use created_at as uploaded_at
        )
