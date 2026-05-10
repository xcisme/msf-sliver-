"""Sliver API endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user as get_user
from app.core.database import get_db
from app.models.user import User
from app.services.sliver_service import sliver_service
from app.services.log_service import add_log
from app.schemas.sliver import (
    SliverSession,
    CommandRequest,
    CommandResponse,
    ImplantGenerateRequest,
    ImplantGenerateResponse
)

router = APIRouter(prefix="/api/sliver", tags=["sliver"])
logger = logging.getLogger(__name__)


@router.get("/sessions", response_model=list[SliverSession])
async def get_sessions(current_user: User = Depends(get_user)) -> list[SliverSession]:
    """Get Sliver sessions.

    Requires JWT authentication.

    Returns:
        List of Sliver sessions
    """
    return await sliver_service.get_sessions()


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> dict:
    """Delete a Sliver session.

    Requires JWT authentication.

    Args:
        session_id: Session ID to delete

    Returns:
        Success message
    """
    success = await sliver_service.delete_session(session_id)

    # Log session deletion
    add_log(
        db=db,
        user_id=current_user.id,
        action="DELETE_SESSION",
        result="SUCCESS" if success else "FAILED",
        target=f"sliver:{session_id}",
        detail="删除Sliver会话" if success else "会话不存在",
        ip_address=None
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return {"message": "Session deleted successfully"}


@router.post("/session/{session_id}/command", response_model=CommandResponse)
async def execute_command(
    session_id: str,
    req: CommandRequest,
    current_user: User = Depends(get_user)
) -> CommandResponse:
    """Execute command on a Sliver session.

    Requires JWT authentication.

    Args:
        session_id: Target session ID
        req: Command request

    Returns:
        Command output
    """
    return await sliver_service.execute_command(session_id, req.command)


@router.post("/implant/generate", response_model=ImplantGenerateResponse)
async def generate_implant(
    req: ImplantGenerateRequest,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> ImplantGenerateResponse:
    """Generate Sliver implant.

    Requires JWT authentication.

    Args:
        req: Implant generation request

    Returns:
        Generation result with download URL
    """
    result = await sliver_service.generate_implant(req.model_dump())

    # Log implant generation
    add_log(
        db=db,
        user_id=current_user.id,
        action="GENERATE_IMPLANT",
        result="SUCCESS",
        target="sliver",
        detail=f"生成Sliver implant: {req.implant_type} -> {req.output_name}",
        ip_address=None
    )

    return result