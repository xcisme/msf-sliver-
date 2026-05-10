"""Attack task database model."""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class AttackTask(Base):
    """Attack task model for tracking exploit execution."""

    __tablename__ = "attack_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    module_name = Column(String(255), nullable=False)
    payload = Column(String(255), nullable=True)
    options = Column(JSON, nullable=True)  # Store parameters as JSON
    status = Column(String(20), default="pending")  # pending, running, success, failed, timeout
    session_id = Column(String(64), nullable=True)
    output = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<AttackTask(id={self.id}, module={self.module_name}, status={self.status})>"