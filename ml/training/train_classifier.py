import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SEED_METADATA_PATH = ROOT_DIR / "ml" / "data" / "classifier_seed" / "metadata.csv"
SEED_MATERIALS_PATH = ROOT_DIR / "datasets" / "seed_materials.csv"
OUTPUT_PATH = ROOT_DIR / "ml" / "models" / "classifier_demo_model.json"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    metadata_rows = read_rows(SEED_METADATA_PATH)
    material_rows = read_rows(SEED_MATERIALS_PATH)
    labels = sorted({row["material_category"] for row in material_rows})
    counts = Counter(row["material_category"] for row in metadata_rows)
    total = sum(counts.values()) or 1

    artifact = {
        "artifact_type": "demo_classifier_metadata",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "training_mode": "seed_label_metadata_only",
        "warning": "This is not a trained image model. It records demo labels and seed counts until real images and TensorFlow training are added.",
        "labels": labels,
        "label_to_index": {label: index for index, label in enumerate(labels)},
        "class_priors": {label: counts.get(label, 0) / total for label in labels},
        "seed_rows": len(metadata_rows),
        "model_family_target": "MobileNetV3-small int8 TFLite in a later production training run",
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
