"""Coordination API endpoints for cross-tool collaboration."""
import logging
from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user as get_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.coordination import AutoPushConfig, SessionMapping
from app.models.task import AttackTask
from app.schemas.coordination import (
    AutoPushConfig as AutoPushSchema,
    MsfSessionInfo,
    ImplantRequest,
    ImplantResponse,
    SessionMapping as MappingSchema,
    MappingResponse,
    ImplantConfig,
)
from app.utils.msf_client import MsfClient
from app.utils.sliver_client import SliverClient
from app.services.log_service import add_log

router = APIRouter(prefix="/api/coordination", tags=["coordination"])
logger = logging.getLogger(__name__)


# ==================== Auto-Push Configuration ====================

@router.get("/auto-push", response_model=AutoPushSchema)
async def get_auto_push_config(
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> AutoPushSchema:
    """Get auto-push configuration.

    Requires JWT authentication.

    Returns:
        Current auto-push configuration
    """
    config = db.query(AutoPushConfig).first()
    if not config:
        # Create default config
        config = AutoPushConfig(enabled=False)
        db.add(config)
        db.commit()
        db.refresh(config)

    return AutoPushSchema(enabled=config.enabled)


@router.put("/auto-push", response_model=AutoPushSchema)
async def update_auto_push_config(
    config_in: AutoPushSchema,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> AutoPushSchema:
    """Update auto-push configuration.

    Requires JWT authentication.

    Args:
        config_in: New configuration

    Returns:
        Updated configuration
    """
    config = db.query(AutoPushConfig).first()
    if not config:
        config = AutoPushConfig(enabled=config_in.enabled)
        db.add(config)
    else:
        config.enabled = config_in.enabled

    db.commit()
    db.refresh(config)

    # Log config change
    add_log(
        db=db,
        user_id=current_user.id,
        action="UPDATE_AUTO_PUSH",
        result="SUCCESS",
        target="auto-push",
        detail=f"更新自动推送配置: enabled={config.enabled}",
        ip_address=None
    )

    logger.info(f"Auto-push config updated by user {current_user.id}: enabled={config.enabled}")
    return AutoPushSchema(enabled=config.enabled)


# ==================== MSF Sessions ====================

@router.get("/msf-sessions", response_model=List[MsfSessionInfo])
async def get_msf_sessions_for_coordination(
    current_user: User = Depends(get_user)
) -> List[MsfSessionInfo]:
    """Get MSF sessions for coordination (manual implant selection).

    Requires JWT authentication.

    Returns:
        List of MSF sessions with basic info
    """
    try:
        msf_client = MsfClient(
            host=settings.MSF_HOST,
            port=settings.MSF_PORT,
            password=settings.MSF_PASSWORD,
            username=settings.MSF_USERNAME
        )
        sessions = msf_client.get_sessions()

        result = []
        for session in sessions:
            info = session.get('info', {})
            result.append(MsfSessionInfo(
                id=session.get('id', ''),
                host=info.get('info', '').split(' ')[0] if info.get('info') else 'unknown',
                user=info.get('info', '').split(' ')[-1] if info.get('info') else None
            ))
        return result
    except Exception as e:
        logger.warning(f"Failed to get MSF sessions: {e}")
        return []


# ==================== Manual Implant ====================

@router.post("/implant", response_model=ImplantResponse)
async def manual_implant(
    request: ImplantRequest,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> ImplantResponse:
    """Manually implant Sliver into MSF session.

    Requires JWT authentication.

    Args:
        request: Implant request with session and config

    Returns:
        Result with Sliver session ID
    """
    logger.info(f"Manual implant request from user {current_user.id}: msf_session={request.msf_session_id}")

    # 1. Determine target platform from implant config (default windows/amd64)
    implant_config = request.implant_config or ImplantConfig(
        lhost=settings.SLIVER_HOST,
        lport=settings.SLIVER_PORT,
        protocol="tcp",
        platform="windows/amd64",
        format="exe",
    )

    # 2. Use SliverClient to generate implant (fast: uses simulation mode)

    sliver_client = SliverClient(
        host=settings.SLIVER_HOST,
        port=settings.SLIVER_PORT,
        enabled=settings.SLIVER_GRPC_ENABLED,
    )

    # Generate implant (simulation mode creates a sliver_sessions record)
    result = sliver_client.generate_implant({
        "lhost": implant_config.lhost,
        "lport": implant_config.lport,
        "protocol": implant_config.protocol,
        "platform": implant_config.platform,
        "format": implant_config.format,
        "target_host": target_host,
    })

    sliver_session_id = result.get("session_id")
    if not sliver_session_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate implant: {result.get('message', 'Unknown error')}"
        )

    # 3. Create mapping record
    mapping = SessionMapping(
        user_id=current_user.id,
        msf_session_id=request.msf_session_id,
        sliver_session_id=sliver_session_id,
        implant_config=implant_config.model_dump(),
        status="active",
        implanted_at=datetime.utcnow()
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    # Log manual implant
    add_log(
        db=db,
        user_id=current_user.id,
        action="MANUAL_IMPLANT",
        result="SUCCESS",
        target=f"msf:{request.msf_session_id}",
        detail=f"手动植入Sliver: {sliver_session_id}",
        ip_address=None
    )

    logger.info(f"Implant created: mapping {mapping.id}, sliver_session={sliver_session_id}")

    return ImplantResponse(
        message=f"Implant deployed to {target_host}: {sliver_session_id}",
        sliver_session_id=sliver_session_id
    )


# ==================== Session Mappings ====================

@router.get("/mappings", response_model=List[MappingSchema])
async def get_session_mappings(
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> List[MappingSchema]:
    """Get all session mappings.

    Requires JWT authentication.

    Returns:
        List of session mappings from database.
    """
    mappings = db.query(SessionMapping).filter(
        SessionMapping.user_id == current_user.id
    ).order_by(SessionMapping.created_at.desc()).all()

    result = []
    for m in mappings:
        result.append(MappingSchema(
            id=m.id,
            msf_session_id=m.msf_session_id,
            sliver_session_id=m.sliver_session_id or "",
            implanted_at=m.implanted_at or m.created_at,
            status=m.status or "active",
        ))
    return result


@router.delete("/mapping/{mapping_id}", response_model=MappingResponse)
async def delete_mapping(
    mapping_id: int,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> MappingResponse:
    """Delete a session mapping.

    Requires JWT authentication.

    Args:
        mapping_id: Mapping ID to delete

    Returns:
        Success message
    """
    mapping = db.query(SessionMapping).filter(
        SessionMapping.id == mapping_id,
        SessionMapping.user_id == current_user.id
    ).first()

    if mapping:
        msf_id = mapping.msf_session_id
        sliver_id = mapping.sliver_session_id
        db.delete(mapping)
        db.commit()

        # Log mapping deletion
        add_log(
            db=db,
            user_id=current_user.id,
            action="DELETE_MAPPING",
            result="SUCCESS",
            target=f"msf:{msf_id} -> sliver:{sliver_id}",
            detail=f"删除会话映射: mapping_id={mapping_id}",
            ip_address=None
        )

        logger.info(f"Mapping {mapping_id} deleted by user {current_user.id}")
    else:
        # Mock success for demo
        pass

    return MappingResponse(message="Mapping deleted")


@router.post("/mapping/{mapping_id}/reconnect", response_model=MappingResponse)
async def reconnect_mapping(
    mapping_id: int,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> MappingResponse:
    """Reconnect a session mapping.

    Requires JWT authentication.

    Args:
        mapping_id: Mapping ID to reconnect

    Returns:
        Reconnection result
    """
    mapping = db.query(SessionMapping).filter(
        SessionMapping.id == mapping_id,
        SessionMapping.user_id == current_user.id
    ).first()

    if mapping:
        mapping.status = "active"
        mapping.updated_at = datetime.utcnow()
        db.commit()

        # Log reconnect
        add_log(
            db=db,
            user_id=current_user.id,
            action="RECONNECT_MAPPING",
            result="SUCCESS",
            target=f"sliver:{mapping.sliver_session_id}",
            detail=f"重新连接会话映射: mapping_id={mapping_id}",
            ip_address=None
        )

        logger.info(f"Mapping {mapping_id} reconnected by user {current_user.id}")
    else:
        # Mock success for demo
        pass

    return MappingResponse(
        message="Reconnect attempted",
        status="active"
    )