"""Pydantic models for log API."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class LogItem(BaseModel):
    """Log item model."""
    id: int
    user_id: int
    username: str
    action: str
    target: Optional[str] = None
    result: str
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LogListResponse(BaseModel):
    """Log list response model."""
    total: int
    items: List[LogItem]