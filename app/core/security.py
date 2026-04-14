"""Supabase JWT verification — HS256 with aud + iss checks."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import jwt

from app.core.config import settings

logger = logging.getLogger(__name__)


def supabase_jwt_issuer() -> str:
    """Expected JWT iss claim: https://<project-ref>.supabase.co/auth/v1"""
    if settings.SUPABASE_JWT_ISSUER.strip():
        return settings.SUPABASE_JWT_ISSUER.strip().rstrip("/")
    if not settings.SUPABASE_URL:
        return ""
    parsed = urlparse(settings.SUPABASE_URL.strip())
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}/auth/v1"


def decode_supabase_token(token: str) -> dict | None:
    """Verify Supabase access token (aud + iss + signature + exp).

    Returns payload dict on success, None on any failure.
    """
    if not settings.SUPABASE_JWT_SECRET:
        logger.error("SUPABASE_JWT_SECRET is not configured")
        return None
    issuer = supabase_jwt_issuer()
    if not issuer:
        logger.error("SUPABASE_URL is not configured; cannot verify JWT issuer")
        return None
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            issuer=issuer,
            options={
                "require": ["exp", "sub", "aud", "iss"],
                "verify_aud": True,
                "verify_iss": True,
            },
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Supabase token expired")
        return None
    except jwt.InvalidTokenError as exc:
        logger.debug("Supabase token invalid: %s", exc)
        return None
