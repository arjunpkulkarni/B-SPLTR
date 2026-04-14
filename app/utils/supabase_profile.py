"""Extract profile-related fields from Supabase JWT claims."""

from __future__ import annotations

import uuid
from typing import Any

from app.utils.phone import normalize_to_e164


def email_from_supabase_claims(claims: dict[str, Any], user_id: uuid.UUID) -> str:
    email = claims.get("email")
    if isinstance(email, str) and email.strip():
        return email.strip()
    um = claims.get("user_metadata")
    if isinstance(um, dict):
        e = um.get("email")
        if isinstance(e, str) and e.strip():
            return e.strip()
    return f"{user_id}@supabase.users"


def phone_e164_from_supabase_claims(claims: dict[str, Any]) -> str | None:
    """Return E.164 phone if present and parseable; otherwise None."""
    candidates: list[str] = []
    p = claims.get("phone")
    if isinstance(p, str) and p.strip():
        candidates.append(p.strip())
    um = claims.get("user_metadata")
    if isinstance(um, dict):
        up = um.get("phone")
        if isinstance(up, str) and up.strip():
            candidates.append(up.strip())
    for raw in candidates:
        try:
            return normalize_to_e164(raw)
        except ValueError:
            continue
    return None
