"""
ProjectDocument model for document storage and access control
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.project import AccessLevel
import enum


class DocType(str, enum.Enum):
    """Document type enumeration"""
    TEASER = "teaser"
    IM = "IM"
    FINANCIAL_MODEL = "financial_model"
    PERMIT = "permit"
    RENDER_PDF = "render_pdf"
    OTHER = "other"


class ProjectDocument(BaseModel):
    """ProjectDocument model for managing project-related documents"""

    __tablename__ = "project_documents"

    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    doc_type = Column(SQLEnum(DocType, name='doc_type_enum'), nullable=False)
    file_url = Column(String(1000), nullable=False)
    access_level = Column(SQLEnum(AccessLevel, name='access_level_enum', create_type=False), nullable=False)
    checksum = Column(String(64), nullable=True)  # SHA-256 for integrity verification
    description = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="documents")

    def __repr__(self):
        return f"<ProjectDocument(id={self.id}, project_id={self.project_id}, doc_type={self.doc_type})>"
