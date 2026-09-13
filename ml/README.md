# ML Pipeline

This folder contains the Phase 5 demo ML pipeline for the SIH e-waste platform.

The current project has only seed/sample data, not a real field dataset. Because of that, the scripts create clearly labelled demo artifacts and do not claim production accuracy.

## Scripts

- `training/train_classifier.py`: builds a demo material classification metadata artifact from seed labels.
- `training/train_valuation_model.py`: trains a valuation pipeline. If scikit-learn is installed, it also writes a GradientBoostingRegressor artifact. Without scikit-learn, it writes a transparent JSON baseline from seed prices.
- `training/export_tflite.py`: exports mobile metadata and attempts TensorFlow Lite export only if TensorFlow and a compatible model are available.
- `evaluation/evaluate_models.py`: produces a demo evaluation report without claiming real-world performance.

## Local Commands

```bash
python3 ml/training/train_classifier.py
python3 ml/training/train_valuation_model.py
python3 ml/training/export_tflite.py
python3 ml/evaluation/evaluate_models.py
```

Generated artifacts are written to `ml/models/`.
