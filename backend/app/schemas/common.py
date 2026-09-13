from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field


PositiveDecimal = Annotated[Decimal, Field(gt=0)]


class APIMessage(BaseModel):
    message: str


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


def point_wkt(point: GeoPoint | None) -> str | None:
    if point is None:
        return None
    return f"SRID=4326;POINT({point.longitude} {point.latitude})"
