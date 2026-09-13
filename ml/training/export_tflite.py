import json
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
CLASSIFIER_ARTIFACT_PATH = ROOT_DIR / "ml" / "models" / "classifier_demo_model.json"
EXPORT_MANIFEST_PATH = ROOT_DIR / "ml" / "models" / "tflite_export_manifest.json"
LABELS_PATH = ROOT_DIR / "ml" / "models" / "classifier_labels.txt"
TFLITE_OUTPUT_PATH = ROOT_DIR / "ml" / "models" / "ewaste_classifier_int8.tflite"


def main() -> None:
    if not CLASSIFIER_ARTIFACT_PATH.exists():
        raise SystemExit("classifier_demo_model.json is missing. Run train_classifier.py first.")

    classifier_artifact = json.loads(CLASSIFIER_ARTIFACT_PATH.read_text(encoding="utf-8"))
    labels = classifier_artifact["labels"]
    LABELS_PATH.write_text("\n".join(labels) + "\n", encoding="utf-8")

    try:
        import tensorflow as tf  # noqa: F401

        tflite_status = "skipped: no trained TensorFlow image model is available to convert yet"
    except ImportError:
        tflite_status = "skipped: TensorFlow is not installed in this environment"

    manifest = {
        "artifact_type": "tflite_export_manifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "labels_path": str(LABELS_PATH.relative_to(ROOT_DIR)),
        "target_tflite_path": str(TFLITE_OUTPUT_PATH.relative_to(ROOT_DIR)),
        "tflite_status": tflite_status,
        "warning": "No fake .tflite file is created. A real TFLite export requires a trained TensorFlow image model.",
    }
    EXPORT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {LABELS_PATH}")
    print(f"wrote {EXPORT_MANIFEST_PATH}")
    print(tflite_status)


if __name__ == "__main__":
    main()
