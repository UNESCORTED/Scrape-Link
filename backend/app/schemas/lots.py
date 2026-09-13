from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import GeoPoint, PositiveDecimal


LotStatus = Literal["draft", "listed", "matched", "handed_over", "completed", "disputed"]
SyncStatus = Literal["pending", "synced", "conflict"]


class LotCreate(BaseModel):
    lot_id: UUID
    collector_id: UUID
    material_category: str = Field(min_length=1, max_length=80)
    sub_category: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    image_ref: str | None = Field(default=None, max_length=500)
    approx_weight_kg: PositiveDecimal
    condition: str | None = Field(default=None, max_length=80)
    source_type: str | None = Field(default=None, max_length=80)
    estimated_value: Decimal | None = None
    quoted_price: Decimal | None = None
    final_sale_value: Decimal | None = None
    collection_location: GeoPoint | None = None
    collection_timestamp: datetime | None = None
    status: LotStatus = "draft"
    sync_status: SyncStatus = "pending"


class LotUpdate(BaseModel):
    material_category: str | None = Field(default=None, min_length=1, max_length=80)
    sub_category: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    image_ref: str | None = Field(default=None, max_length=500)
    approx_weight_kg: PositiveDecimal | None = None
    condition: str | None = Field(default=None, max_length=80)
    source_type: str | None = Field(default=None, max_length=80)
    estimated_value: Decimal | None = None
    quoted_price: Decimal | None = None
    final_sale_value: Decimal | None = None
    collection_location: GeoPoint | None = None
    collection_timestamp: datetime | None = None
    status: LotStatus | None = None
    sync_status: SyncStatus | None = None


class LotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lot_id: UUID
    collector_id: UUID | None = None
    material_category: str
    sub_category: str | None = None
    description: str | None = None
    image_ref: str | None = None
    approx_weight_kg: Decimal
    condition: str | None = None
    source_type: str | None = None
    estimated_value: Decimal | None = None
    quoted_price: Decimal | None = None
    final_sale_value: Decimal | None = None
    collection_timestamp: datetime | None = None
    status: LotStatus | None = None
    sync_status: SyncStatus | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
