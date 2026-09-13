from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AnomalyResult:
    is_anomaly: bool
    reason: str
    ratio: Decimal | None = None


def detect_price_anomaly(
    quoted_price: Decimal | None,
    final_price: Decimal | None,
    category_median_price: Decimal | None,
    tolerance_ratio: Decimal = Decimal("0.35"),
) -> AnomalyResult:
    observed = final_price if final_price is not None else quoted_price
    if observed is None or category_median_price is None or category_median_price <= 0:
        return AnomalyResult(is_anomaly=False, reason="insufficient_data")

    ratio = (observed - category_median_price) / category_median_price
    if abs(ratio) > tolerance_ratio:
        return AnomalyResult(is_anomaly=True, reason="price_outside_expected_range", ratio=ratio)
    return AnomalyResult(is_anomaly=False, reason="within_expected_range", ratio=ratio)
