import csv
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
CLASSIFIER_ARTIFACT_PATH = ROOT_DIR / "ml" / "models" / "classifier_demo_model.json"
VALUATION_ARTIFACT_PATH = ROOT_DIR / "ml" / "models" / "valuation_demo_model.json"
TRANSACTIONS_PATH = ROOT_DIR / "datasets" / "seed_transactions.csv"
REPORT_PATH = ROOT_DIR / "ml" / "models" / "evaluation_report.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    classifier = json.loads(CLASSIFIER_ARTIFACT_PATH.read_text(encoding="utf-8"))
    valuation = json.loads(VALUATION_ARTIFACT_PATH.read_text(encoding="utf-8"))
    transactions = read_csv(TRANSACTIONS_PATH)

    labels = set(classifier["labels"])
    categories_in_transactions = {row["material_category"] for row in transactions}
    missing_categories = sorted(categories_in_transactions - labels)

    absolute_errors: list[Decimal] = []
    for row in transactions:
        category_price = valuation["category_unit_prices"].get(row["material_category"])
        if category_price is None:
            continue
        predicted = Decimal(category_price) * Decimal(row["approx_weight_kg"])
        actual = Decimal(row["final_price"])
        absolute_errors.append(abs(predicted - actual))

    mean_absolute_error = None
    if absolute_errors:
        mean_absolute_error = str((sum(absolute_errors, Decimal("0")) / Decimal(len(absolute_errors))).quantize(Decimal("0.01")))

    report = {
        "artifact_type": "demo_evaluation_report",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "warning": "This report uses tiny seed data only. It is not a real-world model accuracy report.",
        "classifier_label_count": len(labels),
        "classifier_seed_categories_missing_from_labels": missing_categories,
        "valuation_seed_transaction_count": len(transactions),
        "valuation_demo_mean_absolute_error_on_seed_transactions": mean_absolute_error,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {REPORT_PATH}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
