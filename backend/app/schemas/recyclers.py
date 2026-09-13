from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import GeoPoint


AuthorizationStatus = Literal["authorized", "pending", "unverified", "suspended"]


class RecyclerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    facility_location: GeoPoint
    service_area_radius_km: Decimal = Field(default=15, gt=0)
    materials_accepted: list[str] = Field(min_length=1)
    authorization_id: str | None = Field(default=None, max_length=120)
    authorization_status: AuthorizationStatus = "unverified"
    contact_phone: str | None = Field(default=None, max_length=20)
    offered_rates: dict[str, Decimal] | None = None
    pickup_available: bool = False


class RecyclerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    facility_location: GeoPoint | None = None
    service_area_radius_km: Decimal | None = Field(default=None, gt=0)
    materials_accepted: list[str] | None = Field(default=None, min_length=1)
    authorization_id: str | None = Field(default=None, max_length=120)
    authorization_status: AuthorizationStatus | None = None
    contact_phone: str | None = Field(default=None, max_length=20)
    offered_rates: dict[str, Decimal] | None = None
    pickup_available: bool | None = None


class RecyclerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recycler_id: UUID
    name: str
    service_area_radius_km: Decimal | None = None
    materials_accepted: list[str]
    authorization_id: str | None = None
    authorization_status: AuthorizationStatus | None = None
    contact_phone: str | None = None
    offered_rates: dict | None = None
    pickup_available: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
