"""Auth routes: Supabase JWT + local profile (users table)."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_supabase_jwt
from app.db.session import get_db
from app.models.user import User
from app.core.response import success_response
from app.schemas.auth import CreateProfileRequest, UserBrief
from app.utils.supabase_profile import email_from_supabase_claims, phone_e164_from_supabase_claims

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return success_response(data=UserBrief.model_validate(current_user).model_dump())


@router.post("/create-profile")
def create_profile(
    body: CreateProfileRequest,
    db: Session = Depends(get_db),
    ctx=Depends(get_supabase_jwt),
):
    """First-time onboarding: create the local profile row (id = Supabase user id).

    Idempotent: if a row already exists, returns it without overwriting.
    """
    existing = db.query(User).filter(User.id == ctx.user_id).first()
    if existing:
        return success_response(
            data=UserBrief.model_validate(existing).model_dump(),
            message="Profile already exists",
        )

    email = email_from_supabase_claims(ctx.claims, ctx.user_id)
    phone = phone_e164_from_supabase_claims(ctx.claims)

    user = User(
        id=ctx.user_id,
        email=email,
        full_name=body.full_name.strip(),
        phone=phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("auth.create_profile user_id=%s phone=%s", user.id, phone)
    return success_response(
        data=UserBrief.model_validate(user).model_dump(),
        message="Profile created",
    )


@router.post("/logout")
def logout(_ctx=Depends(get_supabase_jwt)):
    """No-op server-side — valid JWT required so anonymous callers cannot spam."""
    return success_response(message="Logged out successfully")
