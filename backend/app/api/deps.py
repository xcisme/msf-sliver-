"""API dependencies for authentication and authorization."""
from jose import jwt, JWTError, ExpiredSignatureError

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User

# HTTPBearer security scheme for Swagger Bearer Token input
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Verify JWT token and get current user.

    Args:
        credentials: HTTP Authorization credentials containing Bearer token

    Returns:
        User object from database

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Query user from database
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user
        finally:
            db.close()

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
