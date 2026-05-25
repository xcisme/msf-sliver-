"""Pydantic models for Sliver API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SliverSession(BaseModel):
    """Sliver session model."""
    id: str
    host: str = ""
    user: str = ""
    platform: str = ""
    created_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    status: str = "active"

    model_config = ConfigDict(from_attributes=True)


class CommandRequest(BaseModel):
    """Command execution request model."""
    command: str


class CommandResponse(BaseModel):
    """Command execution response model."""
    output: str


class ImplantGenerateRequest(BaseModel):
    """Implant generation request model."""
    lhost: str
    lport: int
    protocol: str = "tcp"
    platform: str = "windows/amd64"
    format: str = "exe"


class ImplantGenerateResponse(BaseModel):
    """Implant generation response model."""
    message: str
    session_id: Optional[str] = None
    download_url: Optional[str] = None