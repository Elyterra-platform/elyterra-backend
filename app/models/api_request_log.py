"""
ApiRequestLog model for audit trail and legal compliance
"""

from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey
from app.models.base import Base
from datetime import datetime


class ApiRequestLog(Base):
    """ApiRequestLog model for logging API requests (≥12 months retention)"""

    __tablename__ = "api_request_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    endpoint = Column(String(500), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(String(1000), nullable=True)
    status_code = Column(Integer, nullable=True)
    request_duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<ApiRequestLog(id={self.id}, endpoint={self.endpoint}, status={self.status_code})>"
