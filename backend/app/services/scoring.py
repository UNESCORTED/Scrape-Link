from dataclasses import dataclass


@dataclass(frozen=True)
class MatchScoreInputs:
    distance_km: float | None
    offered_rate: float | None
    authorization_status: str | None
    pickup_available: bool | None
    reliability_score: float | None = None


def calculate_match_score(inputs: MatchScoreInputs) -> float:
    distance_component = max(0.0, 1.0 - ((inputs.distance_km or 50.0) / 50.0))
    rate_component = min((inputs.offered_rate or 0.0) / 200.0, 1.0)
    authorization_component = {
        "authorized": 1.0,
        "pending": 0.6,
        "unverified": 0.35,
        "suspended": 0.0,
    }.get(inputs.authorization_status or "unverified", 0.35)
    pickup_component = 1.0 if inputs.pickup_available else 0.0
    reliability_component = inputs.reliability_score if inputs.reliability_score is not None else 0.5

    return round(
        (distance_component * 0.35)
        + (rate_component * 0.25)
        + (authorization_component * 0.20)
        + (pickup_component * 0.10)
        + (reliability_component * 0.10),
        4,
    )
