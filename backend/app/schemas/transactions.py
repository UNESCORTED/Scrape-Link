from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import GeoPoint


PaymentMode = Literal["cash", "digital"]
PaymentStatus = Literal["pending", "paid", "partial"]
TransactionStatus = Literal["initiated", "handed_over", "confirmed", "completed", "flagged"]


class TransactionCreate(BaseModel):
    transaction_id: UUID | None = None
    lot_id: UUID | None = None
    collector_id: UUID | None = None
    recycler_id: UUID | None = None
    quoted_price: Decimal | None = None
    final_price: Decimal | None = None
    payment_mode: PaymentMode = "cash"
    payment_status: PaymentStatus = "pending"
    transaction_status: TransactionStatus = "initiated"
    handover_location: GeoPoint | None = None
    handover_timestamp: datetime | None = None


class TransactionUpdate(BaseModel):
    quoted_price: Decimal | None = None
    final_price: Decimal | None = None
    payment_mode: PaymentMode | None = None
    payment_status: PaymentStatus | None = None
    transaction_status: TransactionStatus | None = None
    handover_location: GeoPoint | None = None
    handover_timestamp: datetime | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: UUID
    lot_id: UUID | None = None
    collector_id: UUID | None = None
    recycler_id: UUID | None = None
    quoted_price: Decimal | None = None
    final_price: Decimal | None = None
    payment_mode: PaymentMode | None = None
    payment_status: PaymentStatus | None = None
    transaction_status: TransactionStatus | None = None
    handover_timestamp: datetime | None = None
    created_at: datetime | None = None
