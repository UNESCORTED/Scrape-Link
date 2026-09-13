from dataclasses import dataclass

from app.ml.artifacts import load_classifier_artifact
from app.models.material_lot import MaterialLot


@dataclass(frozen=True)
class ClassificationResult:
    material_category: str
    confidence: float
    method: str


async def classify_lot(lot: MaterialLot) -> ClassificationResult:
    artifact = load_classifier_artifact()
    if artifact and lot.material_category in artifact.get("labels", []):
        priors = artifact.get("class_priors", {})
        return ClassificationResult(
            material_category=lot.material_category,
            confidence=float(priors.get(lot.material_category, 0.0)),
            method="phase5_demo_classifier_metadata",
        )
    return ClassificationResult(
        material_category=lot.material_category,
        confidence=0.0,
        method="fallback_existing_lot_category_no_classifier_artifact",
    )


async def classify_lot_placeholder(lot: MaterialLot) -> ClassificationResult:
    return await classify_lot(lot)
