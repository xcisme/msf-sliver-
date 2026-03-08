"""Metasploit Framework API endpoints."""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.api import deps
from app.api.deps import get_current_user
from app.core.config import settings
from app.utils.msf_client import MsfClient

router = APIRouter(prefix="/api/msf", tags=["msf"])

logger = logging.getLogger(__name__)


@router.get("/test")
async def test_msf_connection() -> Dict[str, Any]:
    """Test MSF RPC connection.

    Returns:
        Connection status information
    """
    try:
        msf_client = MsfClient(
            host=settings.MSF_HOST,
            port=settings.MSF_PORT,
            password=settings.MSF_PASSWORD,
            username=settings.MSF_USERNAME
        )
        result = msf_client.test_connection()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to connect to MSF: {str(e)}",
            "sessions_count": 0
        }


@router.get("/sessions")
async def get_sessions(current_user: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Get active MSF sessions.

    Requires JWT authentication.

    Args:
        current_user: Authenticated user from token

    Returns:
        List of active sessions
    """
    try:
        msf_client = MsfClient(
            host=settings.MSF_HOST,
            port=settings.MSF_PORT,
            password=settings.MSF_PASSWORD,
            username=settings.MSF_USERNAME
        )
        sessions = msf_client.get_sessions()
        return {
            "status": "success",
            "sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def stop_session(
    session_id: int,
    current_user: str = Depends(deps.get_current_user)
) -> Dict[str, Any]:
    """Stop a specific MSF session.

    Requires JWT authentication.

    Args:
        session_id: The ID of the session to stop
        current_user: Authenticated user from token

    Returns:
        Result of stopping the session

    Raises:
        HTTPException: If session doesn't exist or stopping fails
    """
    try:
        msf_client = MsfClient(
            host=settings.MSF_HOST,
            port=settings.MSF_PORT,
            password=settings.MSF_PASSWORD,
            username=settings.MSF_USERNAME
        )
        result = msf_client.stop_session(session_id)

        # 如果返回状态是 error，抛出 HTTP 异常
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "Session not found")
            )

        return result
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"Failed to stop session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop session: {str(e)}"
        )


@router.post("/exploit", response_model=dict)
async def execute_exploit(
    request: dict,
    current_user: str = Depends(deps.get_current_user)
):
    """
    执行exploit模块

    请求格式：
    {
        "module": "exploit/multi/handler",  # 必需
        "payload": "windows/x64/meterpreter/reverse_tcp",  # 可选
        "options": {  # 可选
            "LHOST": "192.168.1.1",
            "LPORT": "4444"
        }
    }
    """
    module = request.get("module")
    options = request.get("options", {})
    payload = request.get("payload")  # 从请求中获取payload

    if not module:
        raise HTTPException(status_code=400, detail="module is required")

    # 记录日志（便于调试）
    logger.info(f"Executing exploit: module={module}, payload={payload}, options={options}")

    try:
        client = MsfClient(
            host=settings.MSF_HOST,
            port=settings.MSF_PORT,
            password=settings.MSF_PASSWORD
        )

        result = client.execute_exploit(module, options, payload)
        return result

    except Exception as e:
        logger.error(f"Exploit execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modules/{module_type}")
async def get_modules(
    module_type: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get available MSF modules.

    Requires JWT authentication.

    Args:
        module_type: Type of module (exploit, auxiliary, payload, post)
        current_user: Authenticated user from token

    Returns:
        List of available modules
    """
    valid_types = ["exploit", "auxiliary", "payload", "post"]
    if module_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid module type. Must be one of: {', '.join(valid_types)}"
        )

    try:
        msf_client = MsfClient(
            host=settings.MSF_HOST,
            port=settings.MSF_PORT,
            password=settings.MSF_PASSWORD,
            username=settings.MSF_USERNAME
        )
        modules = msf_client.get_modules(module_type)
        return {
            "status": "success",
            "module_type": module_type,
            "modules": modules,
            "count": len(modules)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get modules: {str(e)}"
        )
