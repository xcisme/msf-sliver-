"""Pydantic models for MSF API."""
from typing import Dict, List, Optional

from pydantic import BaseModel


class ModuleInfo(BaseModel):
    """Module information model."""
    name: str
    fullname: str
    description: str
    rank: int
    type: str


class ModuleOption(BaseModel):
    """Module option/parameter model."""
    name: str
    required: bool
    default: Optional[str] = None
    description: str
    type: Optional[str] = None


class ExploitRequest(BaseModel):
    """Exploit execution request model."""
    module: str
    payload: Optional[str] = None
    options: Optional[Dict[str, str]] = {}


class ExploitResponse(BaseModel):
    """Exploit execution response model."""
    success: bool
    message: str
    session_id: Optional[str] = None
    output: Optional[Dict] = None
    job_id: Optional[int] = None
