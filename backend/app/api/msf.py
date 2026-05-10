"""Metasploit Framework API endpoints."""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api import deps
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.msf import ExploitRequest, ExploitResponse, ModuleInfo, ModuleOption
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


@router.post("/exploit", response_model=ExploitResponse)
async def execute_exploit(
    request: ExploitRequest,
    current_user: str = Depends(deps.get_current_user)
) -> ExploitResponse:
    """Execute an exploit or auxiliary module.

    Requires JWT authentication.

    Args:
        request: Exploit request containing module, payload, and options
        current_user: Authenticated user from token

    Returns:
        Execution result with session_id if successful
    """
    if not request.module:
        raise HTTPException(status_code=400, detail="module is required")

    # 记录日志
    logger.info(f"User {current_user} executing exploit: module={request.module}, payload={request.payload}, options={request.options}")

    try:
        msf_client = MsfClient(
            host=settings.MSF_HOST,
            port=settings.MSF_PORT,
            password=settings.MSF_PASSWORD,
            username=settings.MSF_USERNAME
        )

        result = msf_client.execute_exploit(
            module_path=request.module,
            options=request.options or {},
            payload=request.payload
        )

        # 返回标准化响应
        return ExploitResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            session_id=result.get("session_id"),
            output=result.get("output"),
            job_id=result.get("job_id")
        )

    except Exception as e:
        logger.error(f"Exploit execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exploit execution failed: {str(e)}"
        )


@router.get("/modules", response_model=Dict[str, Any])
async def get_modules(
    type: str = Query(None, description="Module type: exploit, auxiliary, payload, encoder, nop, post"),
    keyword: str = Query(None, description="Keyword for fuzzy search in module names"),
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get list of available MSF modules with metadata.

    Requires JWT authentication.

    Args:
        type: Optional module type. If not specified, returns all module types.
        keyword: Optional keyword for fuzzy matching module names.
        current_user: Authenticated user from token

    Returns:
        List of module information with details
    """
    valid_types = ["exploit", "auxiliary", "payload", "encoder", "nop", "post"]
    if type is not None and type not in valid_types:
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
        modules = msf_client.get_modules(module_type=type, keyword=keyword)
        return {
            "modules": modules,
            "count": len(modules)
        }
    except Exception as e:
        logger.error(f"Failed to get modules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to MSF: {str(e)}"
        )


@router.get("/modules/options", response_model=List[ModuleOption])
async def get_module_options(
    module_name: str = Query(..., description="Full module path, e.g., exploit/multi/handler"),
    payload: Optional[str] = Query(None, description="Payload name, e.g., windows/x64/meterpreter/reverse_tcp"),
    current_user: str = Depends(get_current_user)
) -> List[ModuleOption]:
    """Get options/parameters for a specific module, optionally merged with payload options.

    Requires JWT authentication.

    Args:
        module_name: Full module path (use query parameter to handle slashes)
        payload: Optional payload name to merge with module options
        current_user: Authenticated user from token

    Returns:
        List of module options
    """
    try:
        msf_client = MsfClient(
            host=settings.MSF_HOST,
            port=settings.MSF_PORT,
            password=settings.MSF_PASSWORD,
            username=settings.MSF_USERNAME
        )
        options = msf_client.get_module_options(module_name, payload)
        return options
    except Exception as e:
        logger.error(f"Failed to get options for module {module_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get module options: {str(e)}"
        )


@router.get("/modules/compatible_payloads")
async def get_compatible_payloads(
    module_name: str = Query(..., description="Exploit module full path, e.g., exploit/multi/handler"),
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get compatible payloads for an exploit module.

    Requires JWT authentication.

    Args:
        module_name: Full exploit module path
        current_user: Authenticated user from token

    Returns:
        List of compatible payload names
    """
    try:
        msf_client = MsfClient(
            host=settings.MSF_HOST,
            port=settings.MSF_PORT,
            password=settings.MSF_PASSWORD,
            username=settings.MSF_USERNAME
        )
        payloads = msf_client.get_compatible_payloads(module_name)
        return {
            "payloads": payloads,
            "count": len(payloads)
        }
    except Exception as e:
        logger.error(f"Failed to get compatible payloads for module {module_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get compatible payloads: {str(e)}"
        )


@router.get("/modules/{module_type}")
async def get_modules(
    module_type: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get available MSF modules (names only).

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
