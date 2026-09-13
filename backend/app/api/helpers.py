from collections.abc import Iterable
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import Principal
from app.schemas.common import GeoPoint, point_wkt


def ensure_collector_access(principal: Principal, collector_id: UUID | None) -> None:
    if principal.role == "collector" and principal.collector_id != collector_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Collector cannot access this record")


def ensure_recycler_access(principal: Principal, recycler_id: UUID | None) -> None:
    if principal.role == "recycler" and principal.recycler_id != recycler_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recycler cannot access this record")


def clean_update(data: dict, excluded: Iterable[str] = ()) -> dict:
    excluded_set = set(excluded)
    return {key: value for key, value in data.items() if key not in excluded_set and value is not None}


async def commit_refresh(session: AsyncSession, instance: object) -> object:
    await session.commit()
    await session.refresh(instance)
    return instance


def extract_point(data: dict, field_name: str) -> str | None:
    point = data.pop(field_name, None)
    if isinstance(point, GeoPoint):
        return point_wkt(point)
    return None


def json_ready(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    return value
