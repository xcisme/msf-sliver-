"""Pydantic models for coordination API."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class AutoPushConfig(BaseModel):
    """Auto-push configuration model."""
    enabled: bool = False


class MsfSessionInfo(BaseModel):
    """MSF session info for coordination."""
    id: str
    host: str
    user: Optional[str] = None


class ImplantConfig(BaseModel):
    """Implant configuration model."""
    lhost: str
    lport: int
    protocol: str = "tcp"
    platform: str = "windows/amd64"
    format: str = "exe"


class ImplantRequest(BaseModel):
    """Manual implant request model."""
    msf_session_id: str
    implant_config: ImplantConfig


class ImplantResponse(BaseModel):
    """Manual implant response model."""
    message: str
    sliver_session_id: Optional[str] = None


class SessionMapping(BaseModel):
    """Session mapping model."""
    id: int
    msf_session_id: str
    sliver_session_id: str
    implanted_at: datetime
    status: str  # active, inactive, failed

    model_config = ConfigDict(from_attributes=True)


class MappingResponse(BaseModel):
    """Generic mapping response."""
    message: str
    status: Optional[str] = None