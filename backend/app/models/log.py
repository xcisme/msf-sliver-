"""Operation log database model."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class OperationLog(Base):
    """Operation log model for tracking user actions."""

    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)  # login, logout, execute_exploit, stop_session, etc.
    target = Column(String(255), nullable=True)  # Target resource (module name, session ID, etc.)
    result = Column(String(20), nullable=True)  # success, failed, timeout
    detail = Column(Text, nullable=True)  # Additional details
    ip_address = Column(String(45), nullable=True)  # Client IP
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationship with User
    user = relationship("User", backref="operation_logs")

    def __repr__(self):
        return f"<OperationLog(id={self.id}, action={self.action}, result={self.result})>"