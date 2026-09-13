from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class RecyclerMatchResponse(BaseModel):
    recycler_id: UUID
    name: str
    distance_km: float | None = None
    offered_rate: Decimal | None = None
    authorization_status: Literal["authorized", "pending", "unverified", "suspended"] | None = None
    pickup_available: bool | None = None
    materials_accepted: list[str]
    score: float
