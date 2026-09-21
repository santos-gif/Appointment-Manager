import uuid
from typing import AsyncGenerator, List, Optional
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.security import decode_jwt_token
from app.database import get_db
from app.models.user import User


async def get_optional_current_user(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Extracts user identity from HttpOnly 'access_token' cookie or fallback Bearer header.
    Returns None if unauthenticated.
    """
    token = access_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        return None

    try:
        payload = decode_jwt_token(token)
        if payload.get("token_type") != "access":
            return None
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user_id = uuid.UUID(user_id_str)
        stmt = select(User).where(User.id == user_id, User.is_active == True)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()
    except Exception:
        return None


async def get_current_user(
    user: Optional[User] = Depends(get_optional_current_user),
) -> User:
    """Requires an authenticated user session."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required or access token expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(required_roles: List[str]):
    """Enforces specific organizational or system roles."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user
        user_roles = set(current_user.roles)
        if not (user_roles & set(required_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Insufficient privileges. Required: {required_roles}",
            )
        return current_user
    return role_checker


async def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrative privileges required.",
        )
    return current_user
