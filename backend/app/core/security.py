import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from fastapi import Response
import bcrypt
from app.config import settings


def hash_password(password: str) -> str:
    """Hashes password using native bcrypt with safe 72-byte boundary."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against hashed password using native bcrypt."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_jwt_token(data: Dict[str, Any], expires_delta: timedelta, token_type: str = "access") -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "token_type": token_type,
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: str, email: str, roles: list[str], claims: Optional[Dict[str, Any]] = None) -> str:
    """Creates a 15-minute access token."""
    payload = {
        "sub": user_id,
        "email": email,
        "roles": roles,
        "claims": claims or {},
    }
    return create_jwt_token(payload, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), token_type="access")


def create_refresh_token(user_id: str) -> str:
    """Creates a 7-day refresh token."""
    payload = {"sub": user_id}
    return create_jwt_token(payload, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), token_type="refresh")


def create_escalation_token(intent_id: str, target_resource_id: str, minutes: int = 60) -> str:
    """Creates a secure, one-time escalation token for intent-routed booking."""
    payload = {
        "intent_id": intent_id,
        "target_resource_id": target_resource_id,
    }
    return create_jwt_token(payload, timedelta(minutes=minutes), token_type="escalation")


def decode_jwt_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    """Sets HttpOnly cookies for access token (15m) and refresh token (7d)."""
    # 15 minutes in seconds = 900
    access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    # 7 days in seconds = 604800
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=access_max_age,
        expires=access_max_age,
        path="/",
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=refresh_max_age,
        expires=refresh_max_age,
        path=f"{settings.API_V1_PREFIX}/auth/refresh",
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )


def clear_auth_cookies(response: Response) -> None:
    """Clears authentication cookies."""
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key="refresh_token",
        path=f"{settings.API_V1_PREFIX}/auth/refresh",
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )
