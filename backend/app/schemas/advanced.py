"""Pydantic models for advanced config API."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


# ==================== IP Pool ====================

class IpPoolItem(BaseModel):
    """IP pool item model."""
    id: int
    ip_address: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IpPoolCreate(BaseModel):
    """IP pool create request model."""
    ip_address: str
    description: Optional[str] = None


class IpPoolList(BaseModel):
    """IP pool list response."""
    items: List[IpPoolItem]
    total: int


class IpPoolTestResponse(BaseModel):
    """IP pool test response."""
    selected_ip: str
    message: str


# ==================== Domain DNS ====================

class DomainDnsConfig(BaseModel):
    """Domain DNS configuration model."""
    id: int
    domain: str
    current_ip: Optional[str] = None
    update_interval: int = 300  # seconds
    enabled: bool = False
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DomainDnsUpdate(BaseModel):
    """Domain DNS update request model."""
    domain: str
    update_interval: int = 300
    enabled: bool = False


class DomainDnsManualUpdateResponse(BaseModel):
    """Manual DNS update response."""
    domain: str
    new_ip: str
    message: str


# ==================== Traffic Obfuscation ====================

class TrafficConfig(BaseModel):
    """Traffic obfuscation configuration model."""
    id: int
    encryption: str = "none"  # none, aes256, rc4
    random_headers: bool = False
    data_chunking: bool = False
    chunk_size: int = 1024
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TrafficConfigUpdate(BaseModel):
    """Traffic config update request model."""
    encryption: str = "none"
    random_headers: bool = False
    data_chunking: bool = False
    chunk_size: int = 1024