from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import GeoPoint, PositiveDecimal


class PriceCreate(BaseModel):
    material_category: str = Field(min_length=1, max_length=80)
    sub_category: str | None = Field(default=None, max_length=80)
    location: GeoPoint | None = None
    recorded_date: date
    buying_price: PositiveDecimal
    market_range_min: Decimal | None = None
    market_range_max: Decimal | None = None
    unit: str = Field(default="kg", min_length=1, max_length=20)
    recycler_id: UUID | None = None
    source: str | None = Field(default=None, max_length=120)


class PriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    price_id: int
    material_category: str
    sub_category: str | None = None
    recorded_date: date
    buying_price: Decimal
    market_range_min: Decimal | None = None
    market_range_max: Decimal | None = None
    unit: str | None = None
    recycler_id: UUID | None = None
    source: str | None = None

class PriceTrendResponse(BaseModel):
    count: int
    latest_price: Decimal | None = None
    average_price: Decimal | None = None
    direction: str


class PriceBoardResponse(BaseModel):
    prices: list[PriceResponse]
    trend: PriceTrendResponse
