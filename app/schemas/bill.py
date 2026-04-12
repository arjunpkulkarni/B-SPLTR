import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class BillCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    merchant_name: str | None = None
    currency: str = "USD"
    notes: str | None = None


class BillUpdate(BaseModel):
    title: str | None = None
    merchant_name: str | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    tax: Decimal | None = None
    tip: Decimal | None = None
    service_fee: Decimal | None = None
    total: Decimal | None = None
    notes: str | None = None
    status: str | None = None


class BillOut(BaseModel):
    id: uuid.UUID
    title: str
    merchant_name: str | None = None
    currency: str
    status: str
    owner_id: uuid.UUID
    subtotal: Decimal
    tax: Decimal
    tip: Decimal
    service_fee: Decimal
    total: Decimal
    notes: str | None = None
    member_count: int = 0
    ready_to_pay: bool = False
    ready_reason: str | None = None
    ready_marked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MarkReadyRequest(BaseModel):
    reason: Literal["fully_collected", "owner_override"] = "fully_collected"
    notes: str | None = Field(default=None, max_length=500)


class ReadinessOut(BaseModel):
    bill_id: uuid.UUID
    ready_to_pay: bool
    total_collected: Decimal
    bill_total: Decimal
    collection_pct: Decimal
    meets_threshold: bool
    ready_reason: str | None = None
    ready_marked_at: datetime | None = None
    ready_marked_by: uuid.UUID | None = None


class BillActivity(BaseModel):
    type: str
    description: str
    timestamp: datetime
    actor_name: str | None = None
