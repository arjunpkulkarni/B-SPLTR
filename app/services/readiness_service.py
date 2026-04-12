import logging
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.models.bill import Bill
from app.models.payment import Payment

logger = logging.getLogger(__name__)


class ReadinessService:
    def __init__(self, db: Session):
        self.db = db

    def evaluate(self, bill_id: str) -> dict:
        bill = self.db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            raise ValueError("NOT_FOUND")

        bill_total = bill.total or Decimal("0")

        total_collected = sum(
            (p.amount for p in self._succeeded_payments(bill_id)),
            Decimal("0"),
        )

        if bill_total > 0:
            collection_pct = (
                (total_collected / bill_total) * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            collection_pct = Decimal("0")

        meets_threshold = total_collected >= bill_total and bill_total > 0

        return {
            "bill_id": str(bill.id),
            "ready_to_pay": bill.ready_to_pay,
            "total_collected": total_collected,
            "bill_total": bill_total,
            "collection_pct": collection_pct,
            "meets_threshold": meets_threshold,
            "ready_reason": bill.ready_reason,
            "ready_marked_at": bill.ready_marked_at,
            "ready_marked_by": bill.ready_marked_by,
        }

    def mark_ready(
        self,
        bill_id: str,
        actor_id: str,
        reason: str = "fully_collected",
    ) -> Bill:
        bill = self.db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            raise ValueError("NOT_FOUND")

        if str(bill.owner_id) != actor_id:
            raise ValueError("FORBIDDEN")

        if bill.ready_to_pay:
            raise ValueError("ALREADY_READY")

        if reason == "fully_collected":
            evaluation = self.evaluate(bill_id)
            if not evaluation["meets_threshold"]:
                raise ValueError("THRESHOLD_NOT_MET")

        bill.ready_to_pay = True
        bill.ready_marked_at = datetime.now(timezone.utc)
        bill.ready_marked_by = actor_id  # type: ignore[assignment]
        bill.ready_reason = reason
        bill.status = "ready_to_pay"

        logger.info(
            "bill_readiness_marked",
            extra={
                "bill_id": bill_id,
                "actor_id": actor_id,
                "reason": reason,
            },
        )

        self.db.commit()
        self.db.refresh(bill)
        return bill

    def unmark_ready(self, bill_id: str, actor_id: str) -> Bill:
        bill = self.db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            raise ValueError("NOT_FOUND")
        if str(bill.owner_id) != actor_id:
            raise ValueError("FORBIDDEN")

        bill.ready_to_pay = False
        bill.ready_marked_at = None
        bill.ready_marked_by = None
        bill.ready_reason = None
        bill.status = "active"

        self.db.commit()
        self.db.refresh(bill)
        return bill

    def _succeeded_payments(self, bill_id: str) -> list[Payment]:
        return (
            self.db.query(Payment)
            .filter(Payment.bill_id == bill_id, Payment.status == "succeeded")
            .all()
        )
