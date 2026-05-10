"""Log API endpoints."""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.api.deps import get_current_user as get_user
from app.core.database import get_db
from app.models.user import User
from app.models.log import OperationLog
from app.schemas.log import LogItem, LogListResponse

router = APIRouter(prefix="/api", tags=["logs"])
logger = logging.getLogger(__name__)


@router.get("/logs", response_model=LogListResponse)
async def get_logs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    action: Optional[str] = Query(None, description="Action filter"),
    keyword: Optional[str] = Query(None, description="Keyword search in target or detail"),
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> LogListResponse:
    """Get operation logs with filtering and pagination.

    Requires JWT authentication.

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        start_time: Filter logs from this time
        end_time: Filter logs until this time
        action: Filter by action type
        keyword: Search in target and detail fields

    Returns:
        Paginated log list
    """
    # Start query with eager loading of user relationship
    base_query = db.query(OperationLog).options(joinedload(OperationLog.user))

    # Apply filters
    if start_time:
        base_query = base_query.filter(OperationLog.created_at >= start_time)
    if end_time:
        base_query = base_query.filter(OperationLog.created_at <= end_time)
    if action:
        base_query = base_query.filter(OperationLog.action == action)
    if keyword:
        base_query = base_query.filter(
            or_(
                OperationLog.target.ilike(f"%{keyword}%"),
                OperationLog.detail.ilike(f"%{keyword}%")
            )
        )

    # Get total count (without joinedload)
    total = base_query.count()

    # Get paginated results
    offset = (page - 1) * limit
    logs = base_query.order_by(OperationLog.created_at.desc()).offset(offset).limit(limit).all()

    # Convert to response format
    items = []
    for log in logs:
        items.append(LogItem(
            id=log.id,
            user_id=log.user_id,
            username=log.user.username,
            action=log.action,
            target=log.target,
            result=log.result,
            detail=log.detail,
            ip_address=log.ip_address,
            created_at=log.created_at
        ))

    logger.info(f"User {current_user.id} fetched {len(items)} logs, total: {total}")
    return LogListResponse(total=total, items=items)


@router.get("/logs/actions", response_model=list[str])
async def get_log_actions(
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> list[str]:
    """Get available log action types.

    Requires JWT authentication.

    Returns:
        List of unique action types
    """
    actions = db.query(OperationLog.action).distinct().all()
    return [action[0] for action in actions if action[0]]