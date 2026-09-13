from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import commit_refresh, extract_point
from app.core.auth import Principal, get_current_principal, require_role
from app.db.session import get_db_session
from app.models.price_history import PriceHistory
from app.schemas.prices import PriceBoardResponse, PriceCreate, PriceResponse
from app.services.location_utils import parse_lat_lon
from app.services.pricing_service import (
    PriceFilters,
    list_price_history,
    summarize_price_trend,
)


router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("", response_model=PriceBoardResponse)
async def list_prices(
    category: str | None = Query(default=None),
    location: str | None = Query(default=None, description="Optional latitude,longitude filter"),
    date_range: str | None = Query(default=None, description="Format: YYYY-MM-DD,YYYY-MM-DD"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> PriceBoardResponse:
    if date_range:
        try:
            raw_start, raw_end = date_range.split(",", 1)
            start_date = date.fromisoformat(raw_start) if raw_start else start_date
            end_date = date.fromisoformat(raw_end) if raw_end else end_date
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="date_range must be YYYY-MM-DD,YYYY-MM-DD") from exc
    try:
        parsed_location = parse_lat_lon(location)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    latitude = parsed_location[0] if parsed_location else None
    longitude = parsed_location[1] if parsed_location else None
    prices = await list_price_history(session, PriceFilters(
        category=category,
        start_date=start_date,
        end_date=end_date,
        latitude=latitude,
        longitude=longitude,
        ),
    )

    return PriceBoardResponse(
        prices=[PriceResponse.model_validate(price) for price in prices],
        trend=summarize_price_trend(prices),
    )


@router.post("", response_model=PriceResponse, status_code=status.HTTP_201_CREATED)
async def create_price(
    payload: PriceCreate,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(require_role("recycler")),
) -> PriceHistory:
    if principal.recycler_id and payload.recycler_id and principal.recycler_id != payload.recycler_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recycler cannot create prices for another recycler")
    data = payload.model_dump()
    location_wkt = extract_point(data, "location")
    price = PriceHistory(**data)
    if location_wkt:
        price.location = func.ST_GeogFromText(location_wkt)
    session.add(price)
    return await commit_refresh(session, price)
