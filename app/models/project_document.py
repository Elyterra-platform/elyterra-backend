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
    IM = "IM"
    OM = "OM"
    PITCH_DECK = "pitch_deck"
    FINANCIAL_MODEL = "financial_model"
    LEGAL = "legal"
    BROCHURE = "brochure"
    FLOOR_PLANS = "floor_plans"
    PHOTOS = "photos"
    TEASER = "teaser"
    PERMIT = "permit"
    RENDER_PDF = "render_pdf"
    OTHER = "other"


class ProjectDocument(BaseModel):
    """ProjectDocument model for managing project-related documents"""

    __tablename__ = "project_documents"

    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    file_url = Column(String(1000), nullable=False)  # Full URL to R2 object
    doc_type = Column(SQLEnum(DocType, name='doc_type_enum'), nullable=False)
    access_level = Column(SQLEnum(AccessLevel, name='access_level_enum', create_type=False), nullable=False)
    description = Column(Text, nullable=True)
    checksum = Column(String(255), nullable=True)  # Checksum for integrity verification

    # Relationships
    project = relationship("Project", back_populates="documents")

    def __repr__(self):
        return f"<ProjectDocument(id={self.id}, project_id={self.project_id}, doc_type={self.doc_type})>"
