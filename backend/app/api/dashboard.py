"""Dashboard API endpoints for console overview."""
import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user as get_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.log import OperationLog
from app.schemas.dashboard import MsfSession, SliverSession, OperationLog as LogSchema, LinkStatus, LinkStatusInfo
from app.utils.msf_client import MsfClient

router = APIRouter(prefix="/api", tags=["dashboard"])
logger = logging.getLogger(__name__)


# ==================== MSF Sessions ====================

@router.get("/msf/sessions", response_model=List[MsfSession])
async def get_msf_sessions(
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> List[MsfSession]:
    """Get MSF sessions.

    Requires JWT authentication.

    Returns:
        List of MSF sessions
    """
    try:
        msf_client = MsfClient(
            host=settings.MSF_HOST,
            port=settings.MSF_PORT,
            password=settings.MSF_PASSWORD,
            username=settings.MSF_USERNAME
        )
        sessions = msf_client.get_sessions()

        # Transform to MsfSession format
        result = []
        for session in sessions:
            # Extract session info
            info = session.get('info', {})
            result.append(MsfSession(
                id=session.get('id', ''),
                host=info.get('info', '').split(' ')[0] if info.get('info') else None,
                user=info.get('info', '').split(' ')[-1] if info.get('info') else None,
                platform=info.get('platform'),
                created_at=None,
                last_seen=None,
                status='active',
                local_port=None
            ))
        return result
    except Exception as e:
        logger.warning(f"Failed to get MSF sessions: {e}")
        return []


# ==================== Sliver Sessions ====================

@router.get("/sliver/sessions", response_model=List[SliverSession])
async def get_sliver_sessions(
    current_user: User = Depends(get_user)
) -> List[SliverSession]:
    """Get Sliver sessions.

    Requires JWT authentication.

    Returns:
        List of Sliver sessions (currently returns empty list)
    """
    # TODO: Implement actual Sliver client integration
    return []


# ==================== Recent Logs ====================

@router.get("/logs/recent", response_model=List[LogSchema])
async def get_recent_logs(
    limit: int = Query(5, ge=1, le=100, description="Number of logs to return"),
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> List[LogSchema]:
    """Get recent operation logs.

    Requires JWT authentication.

    Args:
        limit: Number of logs to return (default: 5)
        db: Database session

    Returns:
        List of recent logs
    """
    try:
        logs = db.query(OperationLog).order_by(
            OperationLog.created_at.desc()
        ).limit(limit).all()
        return logs
    except Exception as e:
        logger.warning(f"Failed to get logs: {e}")
        return []


# ==================== Tool Status ====================

@router.get("/status/links", response_model=LinkStatus)
async def get_link_status(
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> LinkStatus:
    """Get connection status of various tools.

    Requires JWT authentication.

    Returns:
        Status of each tool
    """
    # Check MSF connection
    msf_status = "disconnected"
    msf_message = "Not connected"
    msf_host = settings.MSF_HOST
    msf_port = settings.MSF_PORT

    try:
        msf_client = MsfClient(
            host=settings.MSF_HOST,
            port=settings.MSF_PORT,
            password=settings.MSF_PASSWORD,
            username=settings.MSF_USERNAME
        )
        result = msf_client.test_connection()
        if result.get("status") == "success":
            msf_status = "connected"
            sessions_count = result.get('sessions_count', 0)
            msf_message = f"RPC connected - {sessions_count} sessions"
    except Exception as e:
        msf_message = str(e)

    # Sliver (not configured)
    sliver_status = "not_configured"
    sliver_message = "Sliver integration not configured"

    # IP Pool (check if any IP pool exists - placeholder)
    ip_pool_status = "not_configured"
    ip_pool_message = "IP pool not configured"

    return LinkStatus(
        msf_rpc=LinkStatusInfo(
            status=msf_status,
            message=msf_message,
            host=msf_host,
            port=msf_port
        ),
        sliver_grpc=LinkStatusInfo(
            status=sliver_status,
            message=sliver_message
        ),
        ip_pool=LinkStatusInfo(
            status=ip_pool_status,
            message=ip_pool_message
        )
    )