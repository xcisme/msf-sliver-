"""Pydantic models for dashboard API."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class MsfSession(BaseModel):
    """MSF session model."""
    id: str
    host: Optional[str] = None
    user: Optional[str] = None
    platform: Optional[str] = None
    created_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    status: str = "active"
    local_port: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SliverSession(BaseModel):
    """Sliver session model."""
    id: str
    host: Optional[str] = None
    user: Optional[str] = None
    platform: Optional[str] = None
    created_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    status: str = "active"

    model_config = ConfigDict(from_attributes=True)


class OperationLog(BaseModel):
    """Operation log model."""
    id: int
    user_id: int
    action: str
    target: Optional[str] = None
    result: str
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LinkStatusInfo(BaseModel):
    """Link status information for a single tool."""
    status: str  # connected, disconnected, not_configured
    message: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None


class LinkStatus(BaseModel):
    """Overall link status for all tools."""
    msf_rpc: LinkStatusInfo
    sliver_grpc: LinkStatusInfo
    ip_pool: LinkStatusInfo