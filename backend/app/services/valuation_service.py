from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.artifacts import load_valuation_artifact
from app.models.material_lot import MaterialLot
from app.services.pricing_service import latest_category_price


@dataclass(frozen=True)
class ValuationResult:
    estimated_value: Decimal | None
    unit_price: Decimal | None
    method: str


async def estimate_lot_value(session: AsyncSession, lot: MaterialLot) -> ValuationResult:
    artifact = load_valuation_artifact()
    if artifact:
        category_prices = artifact.get("category_unit_prices", {})
        artifact_price = category_prices.get(lot.material_category)
        if artifact_price is not None:
            unit_price = Decimal(str(artifact_price))
            estimated_value = (lot.approx_weight_kg * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return ValuationResult(
                estimated_value=estimated_value,
                unit_price=unit_price,
                method="phase5_demo_valuation_artifact",
            )

    unit_price = await latest_category_price(session, lot.material_category, lot.sub_category)
    if unit_price is None:
        return ValuationResult(estimated_value=None, unit_price=None, method="no_price_history")
    estimated_value = (lot.approx_weight_kg * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return ValuationResult(estimated_value=estimated_value, unit_price=unit_price, method="latest_price_times_weight")
