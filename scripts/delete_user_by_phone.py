"""
Delete a user registered by phone so you can test Get Started again.

Clears FK references, removes bills they own (cascades to receipts, etc.), then deletes the user.

Usage (from repo root, DB reachable as in docker compose):

  docker compose exec api python -m scripts.delete_user_by_phone +19737102530

Also accepts 10-digit US: 9737102530 (normalized to +1…).
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import text

from app.db.session import SessionLocal
from app.models.user import User
from app.utils.phone import normalize_to_e164


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete WealthSplit user by phone (local testing).")
    parser.add_argument("phone", help="Phone number, e.g. +19737102530 or 9737102530")
    args = parser.parse_args()

    raw = args.phone.strip()
    try:
        if raw.isdigit() and len(raw) == 10:
            phone_e164 = normalize_to_e164(f"+1{raw}")
        else:
            phone_e164 = normalize_to_e164(raw)
    except ValueError as e:
        print(f"Invalid phone: {e}", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone_e164).first()
        if not user:
            print(f"No user with phone {phone_e164}")
            return 0

        uid = str(user.id)
        print(f"Deleting user {uid} ({user.email}, {phone_e164}) …")

        # Detach user from shared bills / payments; drop owned bills (DB cascades children).
        db.execute(text("DELETE FROM virtual_cards WHERE created_by = :id"), {"id": uid})
        db.execute(text("UPDATE bill_members SET user_id = NULL WHERE user_id = :id"), {"id": uid})
        db.execute(text("UPDATE payments SET user_id = NULL WHERE user_id = :id"), {"id": uid})
        db.execute(text("UPDATE bills SET ready_marked_by = NULL WHERE ready_marked_by = :id"), {"id": uid})
        db.execute(text("UPDATE sms_logs SET user_id = NULL WHERE user_id = :id"), {"id": uid})
        db.execute(text("DELETE FROM notifications WHERE user_id = :id"), {"id": uid})
        db.execute(text("DELETE FROM bills WHERE owner_id = :id"), {"id": uid})

        db.delete(user)
        db.commit()
        print("Done. You can use Get Started with this number again.")
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
