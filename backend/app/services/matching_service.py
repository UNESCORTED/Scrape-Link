from decimal import Decimal
from typing import Any

from sqlalchemy import Numeric, and_, cast, desc, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material_lot import MaterialLot
from app.models.recycler import Recycler
from app.services.scoring import MatchScoreInputs, calculate_match_score


async def ranked_recycler_matches(
    session: AsyncSession,
    lot: MaterialLot,
    limit: int = 10,
) -> list[dict[str, Any]]:
    if lot.collection_location is None:
        return []

    category = lot.material_category
    offered_rate_expr = cast(Recycler.offered_rates[category].astext, Numeric)
    distance_m_expr = func.ST_Distance(Recycler.facility_location, lot.collection_location)
    in_service_area = func.ST_DWithin(
        Recycler.facility_location,
        lot.collection_location,
        Recycler.service_area_radius_km * 1000,
    )

    statement = (
        select(
            Recycler,
            distance_m_expr.label("distance_meters"),
            offered_rate_expr.label("offered_rate"),
        )
        .where(
            and_(
                Recycler.authorization_status != "suspended",
                Recycler.materials_accepted.any(category),
                in_service_area,
                or_(Recycler.offered_rates.is_(None), Recycler.offered_rates.has_key(category)),  # noqa: W601
            )
        )
        .order_by(desc(offered_rate_expr), distance_m_expr)
        .limit(limit)
    )

    rows = await session.execute(statement)
    matches: list[dict[str, Any]] = []
    for recycler, distance_meters, offered_rate in rows.all():
        distance_km = float(distance_meters / 1000) if distance_meters is not None else None
        rate = float(offered_rate) if offered_rate is not None else None
        score = calculate_match_score(
            MatchScoreInputs(
                distance_km=distance_km,
                offered_rate=rate,
                authorization_status=recycler.authorization_status,
                pickup_available=recycler.pickup_available,
            )
        )
        matches.append(
            {
                "recycler_id": recycler.recycler_id,
                "name": recycler.name,
                "distance_km": round(distance_km, 2) if distance_km is not None else None,
                "offered_rate": Decimal(str(rate)) if rate is not None else None,
                "authorization_status": recycler.authorization_status,
                "pickup_available": recycler.pickup_available,
                "materials_accepted": recycler.materials_accepted,
                "score": score,
            }
        )

    return sorted(matches, key=lambda item: item["score"], reverse=True)


def build_location_point(latitude: float, longitude: float):
    return func.ST_GeogFromText(literal(f"SRID=4326;POINT({longitude} {latitude})"))
