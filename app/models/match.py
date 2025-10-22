"""
Match model for AI-powered investor-developer matching
"""

from sqlalchemy import Column, Integer, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class MatchStatus(str, enum.Enum):
    """Match status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CONTACTED = "contacted"
    CLOSED = "closed"


class Match(BaseModel):
    """Match model for AI matching system"""

    __tablename__ = "matches"

    investor_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    developer_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    match_score = Column(Numeric(5, 2), nullable=True)  # AI confidence 0-100
    status = Column(SQLEnum(MatchStatus, name='match_status_enum'), default=MatchStatus.PENDING, server_default='pending', nullable=False, index=True)

    # Relationships
    investor = relationship("User", foreign_keys=[investor_id], back_populates="investor_matches")
    developer = relationship("User", foreign_keys=[developer_id], back_populates="developer_matches")
    project = relationship("Project", back_populates="matches")

    def __repr__(self):
        return f"<Match(id={self.id}, investor_id={self.investor_id}, project_id={self.project_id}, score={self.match_score})>"
