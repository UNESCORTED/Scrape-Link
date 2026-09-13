from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_history import PriceHistory
from app.services.location_utils import parse_lat_lon
from app.services.matching_service import build_location_point


@dataclass(frozen=True)
class PriceFilters:
    category: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float = 25.0


async def list_price_history(session: AsyncSession, filters: PriceFilters) -> list[PriceHistory]:
    statement = select(PriceHistory).order_by(PriceHistory.recorded_date.desc())
    if filters.category:
        statement = statement.where(PriceHistory.material_category == filters.category)
    if filters.start_date:
        statement = statement.where(PriceHistory.recorded_date >= filters.start_date)
    if filters.end_date:
        statement = statement.where(PriceHistory.recorded_date <= filters.end_date)
    if filters.latitude is not None and filters.longitude is not None:
        point = build_location_point(filters.latitude, filters.longitude)
        statement = statement.where(func.ST_DWithin(PriceHistory.location, point, filters.radius_km * 1000))
    result = await session.execute(statement)
    return list(result.scalars().all())


async def latest_category_price(
    session: AsyncSession,
    category: str,
    sub_category: str | None = None,
) -> Decimal | None:
    statement = (
        select(PriceHistory.buying_price)
        .where(PriceHistory.material_category == category)
        .order_by(PriceHistory.recorded_date.desc())
        .limit(1)
    )
    if sub_category:
        statement = statement.where(PriceHistory.sub_category == sub_category)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


def summarize_price_trend(prices: list[PriceHistory]) -> dict[str, Any]:
    if not prices:
        return {"count": 0, "latest_price": None, "average_price": None, "direction": "unknown"}
    ordered = sorted(prices, key=lambda price: price.recorded_date)
    latest = ordered[-1].buying_price
    average = sum((price.buying_price for price in ordered), Decimal("0")) / Decimal(len(ordered))
    first = ordered[0].buying_price
    if latest > first:
        direction = "up"
    elif latest < first:
        direction = "down"
    else:
        direction = "flat"
    return {
        "count": len(ordered),
        "latest_price": latest,
        "average_price": average.quantize(Decimal("0.01")),
        "direction": direction,
    }
