"""Auth: Supabase JWT validation + optional local profile row."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_supabase_token
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer()


def _http_error(
    status_code: int,
    *,
    code: str,
    message: str,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


@dataclass(frozen=True)
class SupabaseJwtContext:
    """Validated Supabase access token (no local DB row required)."""

    user_id: uuid.UUID
    claims: dict[str, Any]


def get_supabase_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> SupabaseJwtContext:
    """Validate JWT only — use for POST /auth/create-profile before a profile exists."""
    payload = decode_supabase_token(credentials.credentials)
    if payload is None:
        raise _http_error(
            status.HTTP_401_UNAUTHORIZED,
            code="INVALID_TOKEN",
            message="Invalid or expired token",
        )
    sub = payload.get("sub")
    if not sub:
        raise _http_error(
            status.HTTP_401_UNAUTHORIZED,
            code="INVALID_TOKEN",
            message="Token missing subject",
        )
    try:
        user_uuid = uuid.UUID(sub)
    except ValueError:
        raise _http_error(
            status.HTTP_401_UNAUTHORIZED,
            code="INVALID_TOKEN",
            message="Invalid user id in token",
        )
    return SupabaseJwtContext(user_id=user_uuid, claims=payload)


def get_current_user(
    ctx: SupabaseJwtContext = Depends(get_supabase_jwt),
    db: Session = Depends(get_db),
) -> User:
    """Require an existing local profile row (same UUID as auth.users)."""
    user = db.query(User).filter(User.id == ctx.user_id).first()
    if user is None:
        raise _http_error(
            status.HTTP_404_NOT_FOUND,
            code="PROFILE_NOT_FOUND",
            message="No app profile for this account. Complete onboarding first.",
        )
    if not user.is_active:
        raise _http_error(
            status.HTTP_403_FORBIDDEN,
            code="ACCOUNT_DISABLED",
            message="This account is disabled.",
        )
    return user
