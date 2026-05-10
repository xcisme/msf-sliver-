"""Advanced config database models."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func

from app.core.database import Base


class IpPool(Base):
    """IP Pool model."""

    __tablename__ = "ip_pool"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class DomainDnsConfig(Base):
    """Domain DNS configuration model."""

    __tablename__ = "domain_dns_config"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    current_ip = Column(String(45), nullable=True)
    update_interval = Column(Integer, default=300)  # seconds
    enabled = Column(Boolean, default=False)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())


class TrafficObfuscationConfig(Base):
    """Traffic obfuscation configuration model."""

    __tablename__ = "traffic_obfuscation_config"

    id = Column(Integer, primary_key=True, index=True)
    encryption = Column(String(20), default="none")  # none, aes256, rc4
    random_headers = Column(Boolean, default=False)
    data_chunking = Column(Boolean, default=False)
    chunk_size = Column(Integer, default=1024)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())