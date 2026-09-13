from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entry_id: int
    collector_id: UUID | None = None
    transaction_id: UUID | None = None
    amount: Decimal
    entry_type: Literal["earned", "paid", "pending_due"] | None = None
    created_at: datetime | None = None
