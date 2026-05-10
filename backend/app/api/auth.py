"""Authentication API endpoints."""
from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.utils.password import verify_password
from app.services.log_service import add_log

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    """User response model."""
    id: int
    username: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Authenticate user and return JWT token.

    Args:
        login_data: Username and password
        request: HTTP request for client IP
        db: Database session

    Returns:
        Access token and token type

    Raises:
        HTTPException: If credentials are invalid
    """
    # Query user from database
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get client IP
    client_ip = request.client.host if request.client else None

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )

    # Record login success
    add_log(
        db=db,
        user_id=user.id,
        action="LOGIN",
        result="SUCCESS",
        target=user.username,
        detail="用户登录成功",
        ip_address=client_ip
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current authenticated user information.

    Requires JWT authentication.

    Args:
        current_user: Authenticated user from token

    Returns:
        User information

    Raises:
        HTTPException: If token is invalid or user not found
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "created_at": current_user.created_at.isoformat()
    }
