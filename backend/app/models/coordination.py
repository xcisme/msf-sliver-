"""Coordination database models."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class AutoPushConfig(Base):
    """Auto-push configuration model."""

    __tablename__ = "auto_push_config"

    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Boolean, default=False, nullable=False)
    config = Column(JSON, nullable=True)  # Additional config options
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SessionMapping(Base):
    """Session mapping model for MSF to Sliver correlation."""

    __tablename__ = "session_mappings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    msf_session_id = Column(String(64), nullable=False)
    sliver_session_id = Column(String(64), nullable=True)
    implant_config = Column(JSON, nullable=True)  # Store implant configuration
    status = Column(String(20), default="pending")  # pending, active, inactive, failed
    implanted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SessionMapping(id={self.id}, msf={self.msf_session_id}, sliver={self.sliver_session_id}, status={self.status})>"