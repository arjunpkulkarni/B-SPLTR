"""Unit tests for ReadinessService."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.readiness_service import ReadinessService


def _mock_bill(total="100.00", ready=False, owner_id="owner-1"):
    bill = MagicMock()
    bill.id = "bill-1"
    bill.total = Decimal(total)
    bill.ready_to_pay = ready
    bill.ready_reason = None
    bill.ready_marked_at = None
    bill.ready_marked_by = None
    bill.owner_id = owner_id
    bill.status = "active"
    return bill


def _mock_payment(amount="50.00", status="succeeded"):
    p = MagicMock()
    p.amount = Decimal(amount)
    p.status = status
    return p


class TestEvaluate:
    def test_fully_collected(self):
        db = MagicMock()
        bill = _mock_bill(total="100.00")
        db.query.return_value.filter.return_value.first.return_value = bill
        db.query.return_value.filter.return_value.all.return_value = [
            _mock_payment("60.00"),
            _mock_payment("40.00"),
        ]

        svc = ReadinessService(db)
        result = svc.evaluate("bill-1")

        assert result["meets_threshold"] is True
        assert result["total_collected"] == Decimal("100.00")
        assert result["collection_pct"] == Decimal("100.00")

    def test_partially_collected(self):
        db = MagicMock()
        bill = _mock_bill(total="100.00")
        db.query.return_value.filter.return_value.first.return_value = bill
        db.query.return_value.filter.return_value.all.return_value = [
            _mock_payment("30.00"),
        ]

        svc = ReadinessService(db)
        result = svc.evaluate("bill-1")

        assert result["meets_threshold"] is False
        assert result["collection_pct"] == Decimal("30.00")

    def test_zero_total_bill(self):
        db = MagicMock()
        bill = _mock_bill(total="0.00")
        db.query.return_value.filter.return_value.first.return_value = bill
        db.query.return_value.filter.return_value.all.return_value = []

        svc = ReadinessService(db)
        result = svc.evaluate("bill-1")

        assert result["meets_threshold"] is False

    def test_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        svc = ReadinessService(db)
        with pytest.raises(ValueError, match="NOT_FOUND"):
            svc.evaluate("no-such-bill")


class TestMarkReady:
    def test_fully_collected_marks_ready(self):
        db = MagicMock()
        bill = _mock_bill(total="100.00")
        db.query.return_value.filter.return_value.first.return_value = bill
        db.query.return_value.filter.return_value.all.return_value = [
            _mock_payment("100.00"),
        ]

        svc = ReadinessService(db)
        result = svc.mark_ready("bill-1", "owner-1", reason="fully_collected")

        assert result.ready_to_pay is True
        assert result.ready_reason == "fully_collected"
        assert result.status == "ready_to_pay"

    def test_owner_override_bypasses_threshold(self):
        db = MagicMock()
        bill = _mock_bill(total="100.00")
        db.query.return_value.filter.return_value.first.return_value = bill
        db.query.return_value.filter.return_value.all.return_value = [
            _mock_payment("20.00"),
        ]

        svc = ReadinessService(db)
        result = svc.mark_ready("bill-1", "owner-1", reason="owner_override")

        assert result.ready_to_pay is True
        assert result.ready_reason == "owner_override"

    def test_non_owner_forbidden(self):
        db = MagicMock()
        bill = _mock_bill(owner_id="owner-1")
        db.query.return_value.filter.return_value.first.return_value = bill

        svc = ReadinessService(db)
        with pytest.raises(ValueError, match="FORBIDDEN"):
            svc.mark_ready("bill-1", "not-owner", reason="fully_collected")

    def test_threshold_not_met_rejects(self):
        db = MagicMock()
        bill = _mock_bill(total="100.00")
        db.query.return_value.filter.return_value.first.return_value = bill
        db.query.return_value.filter.return_value.all.return_value = [
            _mock_payment("50.00"),
        ]

        svc = ReadinessService(db)
        with pytest.raises(ValueError, match="THRESHOLD_NOT_MET"):
            svc.mark_ready("bill-1", "owner-1", reason="fully_collected")

    def test_already_ready_rejects(self):
        db = MagicMock()
        bill = _mock_bill(ready=True)
        db.query.return_value.filter.return_value.first.return_value = bill

        svc = ReadinessService(db)
        with pytest.raises(ValueError, match="ALREADY_READY"):
            svc.mark_ready("bill-1", "owner-1", reason="fully_collected")
