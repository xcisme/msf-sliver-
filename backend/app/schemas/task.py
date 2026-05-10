"""Pydantic models for attack tasks."""
from datetime import datetime
from typing import Dict, Optional, Any, List

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    """Task creation request model."""
    module_name: str
    payload: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class TaskUpdate(BaseModel):
    """Task update request model."""
    status: Optional[str] = None
    session_id: Optional[str] = None
    output: Optional[str] = None


class TaskResponse(BaseModel):
    """Task response model."""
    id: int
    user_id: int
    module_name: str
    payload: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    status: str
    session_id: Optional[str] = None
    output: Optional[str] = None
    created_at: datetime
    finished_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """Task list response model."""
    total: int
    items: List[TaskResponse]