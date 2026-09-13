import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_MODELS_DIR = ROOT_DIR / "ml" / "models"


def _artifact_path(env_name: str, default_filename: str) -> Path:
    configured = os.getenv(env_name)
    if configured:
        return Path(configured)
    return DEFAULT_MODELS_DIR / default_filename


@lru_cache
def load_classifier_artifact() -> dict[str, Any] | None:
    path = _artifact_path("CLASSIFIER_MODEL_PATH", "classifier_demo_model.json")
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def load_valuation_artifact() -> dict[str, Any] | None:
    path = _artifact_path("VALUATION_MODEL_PATH", "valuation_demo_model.json")
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
