from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class LotClassificationResponse(BaseModel):
    lot_id: UUID
    material_category: str
    category_confidence: float
    estimated_value: Decimal | None = None
    unit_price: Decimal | None = None
    valuation_method: str
    classification_method: str
