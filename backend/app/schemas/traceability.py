from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import GeoPoint


class TraceabilityCreate(BaseModel):
    trace_id: UUID | None = None
    lot_id: UUID | None = None
    photo_refs: list[str] | None = None
    weight_kg: Decimal | None = Field(default=None, gt=0)
    gps_location: GeoPoint | None = None
    captured_at: datetime | None = None
    handover_reference_number: str = Field(min_length=1, max_length=120)
    status_history: list[dict] = Field(default_factory=list)


class TraceabilityConfirm(BaseModel):
    recycler_confirmed_at: datetime | None = None
    status_note: str = "confirmed"


class TraceabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trace_id: UUID
    lot_id: UUID | None = None
    photo_refs: list[str] | None = None
    weight_kg: Decimal | None = None
    captured_at: datetime | None = None
    handover_reference_number: str
    recycler_confirmed: bool | None = None
    recycler_confirmed_at: datetime | None = None
    status_history: list | None = None
