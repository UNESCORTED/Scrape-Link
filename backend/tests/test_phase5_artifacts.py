import json
import unittest
from pathlib import Path

from app.ml.artifacts import DEFAULT_MODELS_DIR


class Phase5ArtifactTests(unittest.TestCase):
    def test_demo_classifier_artifact_is_labelled_as_demo(self):
        artifact_path = DEFAULT_MODELS_DIR / "classifier_demo_model.json"
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        self.assertEqual(artifact["artifact_type"], "demo_classifier_metadata")
        self.assertIn("warning", artifact)
        self.assertGreaterEqual(len(artifact["labels"]), 7)

    def test_tflite_manifest_does_not_claim_fake_export(self):
        manifest_path = DEFAULT_MODELS_DIR / "tflite_export_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["artifact_type"], "tflite_export_manifest")
        self.assertIn("tflite_status", manifest)
        self.assertFalse((Path.cwd() / manifest["target_tflite_path"]).exists())


if __name__ == "__main__":
    unittest.main()
