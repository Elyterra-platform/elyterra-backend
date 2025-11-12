"""
Document Controller
Handles HTTP requests for document endpoints
"""

from fastapi import APIRouter, Depends, File, UploadFile, Form, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.document_service import DocumentService
from app.dto.project_document import (
    DocumentResponseDTO,
    DocumentListResponseDTO,
    DocumentUploadDTO
)
from app.middleware.auth import get_current_user, require_role
from app.models.user import User


router = APIRouter(prefix="/api", tags=["Documents"])


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document to project",
    description="Upload a document to a project. Developer must be project owner."
)
async def upload_document(
    project_id: int,
    file: UploadFile = File(..., description="Document file to upload"),
    doc_type: str = Form(..., description="Document type: IM, OM, pitch_deck, financial_model, legal, brochure, floor_plans, photos, other"),
    access_level: str = Form(default="public", description="Access level: public, verified_only, investor_only"),
    description: Optional[str] = Form(None, description="Document description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("developer"))
):
    """
    Upload document to project

    **Requirements:**
    - Developer role
    - Project owner

    **Supported File Types:**
    - Documents: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX
    - Images: JPG, JPEG, PNG, GIF
    - Videos: MP4, MOV

    **Maximum File Size:** Configured in .env (default: 50MB)

    **Access Levels:**
    - **public**: All authenticated users
    - **verified_only**: Insider tier and above
    - **investor_only**: Capital Partner tier only

    **Returns:** Document metadata with signed URL for immediate download
    """
    # Create metadata DTO
    metadata = DocumentUploadDTO(
        doc_type=doc_type,
        access_level=access_level,
        description=description
    )

    service = DocumentService(db)
    return await service.upload_document(project_id, file, metadata, current_user)


@router.get(
    "/projects/{project_id}/documents",
    response_model=DocumentListResponseDTO,
    summary="List project documents",
    description="Get all documents for a project. Results filtered by user tier."
)
def list_documents(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    List all documents for a project

    **Access Control:**
    - Project owner: See all documents
    - Explorer: Public documents only
    - Insider: Public + Verified_only documents
    - Capital Partner: All documents

    **Note:** Signed URLs not included in list. Use GET /documents/{id} to get signed URL.
    """
    service = DocumentService(db)
    return service.list_documents(project_id, current_user)


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponseDTO,
    summary="Get document with signed URL",
    description="Get document details with temporary signed URL for download"
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get document with signed URL

    **Returns:** Document metadata with signed URL for download

    **Signed URL:**
    - Valid for configured duration (default: 1 hour)
    - Single-use recommended for security
    - Expires at `signed_url_expires_at` timestamp

    **Access Control:**
    - Enforced based on document's access_level and user tier
    """
    service = DocumentService(db)
    return service.get_document(document_id, current_user)


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete document",
    description="Delete document from storage and database. Project owner only."
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("developer"))
):
    """
    Delete document

    **Authorization:** Project owner only

    **Effect:**
    - Deletes file from R2/S3 storage
    - Removes database record
    - Cannot be undone

    **Note:** If storage deletion fails, database record is still removed
    """
    service = DocumentService(db)
    return service.delete_document(document_id, current_user)
