"""Advanced config API endpoints."""
import logging
import random
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user as get_user
from app.core.database import get_db
from app.models.user import User
from app.models.advanced import IpPool, DomainDnsConfig, TrafficObfuscationConfig
from app.schemas.advanced import (
    IpPoolItem,
    IpPoolCreate,
    IpPoolList,
    IpPoolTestResponse,
    DomainDnsConfig as DomainDnsSchema,
    DomainDnsUpdate,
    DomainDnsManualUpdateResponse,
    TrafficConfig,
    TrafficConfigUpdate
)
from app.services.log_service import add_log

router = APIRouter(prefix="/api/config", tags=["advanced"])
logger = logging.getLogger(__name__)


# ==================== IP Pool ====================

@router.get("/ip-pool", response_model=IpPoolList)
async def get_ip_pool(
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> IpPoolList:
    """Get IP pool list.

    Requires JWT authentication.

    Returns:
        List of IP addresses
    """
    items = db.query(IpPool).filter(IpPool.is_active == True).all()
    return IpPoolList(items=items, total=len(items))


@router.post("/ip-pool", response_model=IpPoolItem)
async def add_ip_to_pool(
    ip_data: IpPoolCreate,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> IpPoolItem:
    """Add IP to pool.

    Requires JWT authentication.

    Args:
        ip_data: IP address and description

    Returns:
        Created IP entry
    """
    # Check if IP already exists
    existing = db.query(IpPool).filter(IpPool.ip_address == ip_data.ip_address).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="IP address already exists in pool"
        )

    ip_entry = IpPool(
        ip_address=ip_data.ip_address,
        description=ip_data.description
    )
    db.add(ip_entry)
    db.commit()
    db.refresh(ip_entry)

    # Log IP added to pool
    add_log(
        db=db,
        user_id=current_user.id,
        action="ADD_IP_POOL",
        result="SUCCESS",
        target=ip_data.ip_address,
        detail=f"添加IP到IP池: {ip_data.ip_address}",
        ip_address=None
    )

    logger.info(f"IP {ip_data.ip_address} added to pool by user {current_user.id}")
    return ip_entry


@router.delete("/ip-pool/{ip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ip_from_pool(
    ip_id: int,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
):
    """Delete IP from pool.

    Requires JWT authentication.

    Args:
        ip_id: IP entry ID to delete
    """
    ip_entry = db.query(IpPool).filter(IpPool.id == ip_id).first()
    if not ip_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP entry not found"
        )

    ip_addr = ip_entry.ip_address
    db.delete(ip_entry)
    db.commit()

    # Log IP removed from pool
    add_log(
        db=db,
        user_id=current_user.id,
        action="DELETE_IP_POOL",
        result="SUCCESS",
        target=ip_addr,
        detail=f"从IP池删除IP: {ip_addr}",
        ip_address=None
    )

    logger.info(f"IP {ip_addr} removed from pool by user {current_user.id}")


@router.post("/ip-pool/test", response_model=IpPoolTestResponse)
async def test_ip_pool(
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> IpPoolTestResponse:
    """Test IP pool - randomly select an IP.

    Requires JWT authentication.

    Returns:
        Randomly selected IP
    """
    active_ips = db.query(IpPool).filter(IpPool.is_active == True).all()

    if not active_ips:
        return IpPoolTestResponse(
            selected_ip="",
            message="No active IPs in pool"
        )

    selected = random.choice(active_ips)
    return IpPoolTestResponse(
        selected_ip=selected.ip_address,
        message=f"Randomly selected from {len(active_ips)} IPs"
    )


# ==================== Domain DNS ====================

@router.get("/domain-dns", response_model=DomainDnsSchema)
async def get_domain_dns_config(
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> DomainDnsSchema:
    """Get domain DNS configuration.

    Requires JWT authentication.

    Returns:
        Domain DNS config
    """
    config = db.query(DomainDnsConfig).first()
    if not config:
        # Create default config
        config = DomainDnsConfig(domain="example.com", update_interval=300, enabled=False)
        db.add(config)
        db.commit()
        db.refresh(config)

    return config


@router.put("/domain-dns", response_model=DomainDnsSchema)
async def update_domain_dns_config(
    config_in: DomainDnsUpdate,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> DomainDnsSchema:
    """Update domain DNS configuration.

    Requires JWT authentication.

    Args:
        config_in: New configuration

    Returns:
        Updated configuration
    """
    config = db.query(DomainDnsConfig).first()
    if not config:
        config = DomainDnsConfig(
            domain=config_in.domain,
            update_interval=config_in.update_interval,
            enabled=config_in.enabled
        )
        db.add(config)
    else:
        config.domain = config_in.domain
        config.update_interval = config_in.update_interval
        config.enabled = config_in.enabled

    db.commit()
    db.refresh(config)

    # Log DNS config update
    add_log(
        db=db,
        user_id=current_user.id,
        action="UPDATE_DNS_CONFIG",
        result="SUCCESS",
        target=config.domain,
        detail=f"更新DNS配置: domain={config.domain}, enabled={config.enabled}",
        ip_address=None
    )

    logger.info(f"Domain DNS config updated by user {current_user.id}")
    return config


@router.post("/domain-dns/manual-update", response_model=DomainDnsManualUpdateResponse)
async def manual_dns_update(
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> DomainDnsManualUpdateResponse:
    """Manually update DNS (simulate).

    Requires JWT authentication.

    Returns:
        Update result
    """
    config = db.query(DomainDnsConfig).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain DNS config not found"
        )

    # Get random IP from pool for simulation
    active_ips = db.query(IpPool).filter(IpPool.is_active == True).all()
    if active_ips:
        new_ip = random.choice(active_ips).ip_address
    else:
        new_ip = "192.168.1.100"  # fallback

    config.current_ip = new_ip
    config.updated_at = datetime.utcnow()
    db.commit()

    # Log manual DNS update
    add_log(
        db=db,
        user_id=current_user.id,
        action="MANUAL_DNS_UPDATE",
        result="SUCCESS",
        target=config.domain,
        detail=f"手动更新DNS: {config.domain} -> {new_ip}",
        ip_address=None
    )

    logger.info(f"DNS manually updated to {new_ip} by user {current_user.id}")

    return DomainDnsManualUpdateResponse(
        domain=config.domain,
        new_ip=new_ip,
        message="DNS record updated (simulated)"
    )


# ==================== Traffic Obfuscation ====================

@router.get("/traffic", response_model=TrafficConfig)
async def get_traffic_config(
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> TrafficConfig:
    """Get traffic obfuscation configuration.

    Requires JWT authentication.

    Returns:
        Traffic config
    """
    config = db.query(TrafficObfuscationConfig).first()
    if not config:
        # Create default config
        config = TrafficObfuscationConfig(
            encryption="none",
            random_headers=False,
            data_chunking=False,
            chunk_size=1024
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    return config


@router.put("/traffic", response_model=TrafficConfig)
async def update_traffic_config(
    config_in: TrafficConfigUpdate,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> TrafficConfig:
    """Update traffic obfuscation configuration.

    Requires JWT authentication.

    Args:
        config_in: New configuration

    Returns:
        Updated configuration
    """
    config = db.query(TrafficObfuscationConfig).first()
    if not config:
        config = TrafficObfuscationConfig(
            encryption=config_in.encryption,
            random_headers=config_in.random_headers,
            data_chunking=config_in.data_chunking,
            chunk_size=config_in.chunk_size
        )
        db.add(config)
    else:
        config.encryption = config_in.encryption
        config.random_headers = config_in.random_headers
        config.data_chunking = config_in.data_chunking
        config.chunk_size = config_in.chunk_size
        config.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(config)

    # Log traffic config update
    add_log(
        db=db,
        user_id=current_user.id,
        action="UPDATE_TRAFFIC_CONFIG",
        result="SUCCESS",
        target="traffic",
        detail=f"更新流量混淆配置: encryption={config.encryption}, chunking={config.data_chunking}",
        ip_address=None
    )

    logger.info(f"Traffic config updated by user {current_user.id}")
    return config