"""Authentication API endpoints."""
from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Hardcoded credentials for development
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest) -> Dict[str, Any]:
    """Authenticate user and return JWT token.

    Args:
        login_data: Username and password

    Returns:
        Access token and token type

    Raises:
        HTTPException: If credentials are invalid
    """
    # Verify hardcoded credentials
    if login_data.username != ADMIN_USERNAME or login_data.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": login_data.username},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
