import csv
import json
import pickle
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SEED_PRICES_PATH = ROOT_DIR / "datasets" / "seed_prices.csv"
SEED_TRANSACTIONS_PATH = ROOT_DIR / "datasets" / "seed_transactions.csv"
JSON_OUTPUT_PATH = ROOT_DIR / "ml" / "models" / "valuation_demo_model.json"
SKLEARN_OUTPUT_PATH = ROOT_DIR / "ml" / "models" / "valuation_gradient_boosting.pkl"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def decimal_average(values: list[Decimal]) -> Decimal:
    return sum(values, Decimal("0")) / Decimal(len(values))


def write_json_baseline(price_rows: list[dict[str, str]], transaction_rows: list[dict[str, str]], sklearn_status: str) -> None:
    prices_by_category: dict[str, list[Decimal]] = defaultdict(list)
    for row in price_rows:
        prices_by_category[row["material_category"]].append(Decimal(row["buying_price"]))

    category_unit_prices = {
        category: str(decimal_average(values).quantize(Decimal("0.01")))
        for category, values in sorted(prices_by_category.items())
    }

    transaction_examples = []
    for row in transaction_rows:
        weight = Decimal(row["approx_weight_kg"])
        final_price = Decimal(row["final_price"])
        unit_price = final_price / weight if weight else Decimal("0")
        transaction_examples.append(
            {
                "material_category": row["material_category"],
                "sub_category": row["sub_category"],
                "approx_weight_kg": row["approx_weight_kg"],
                "final_price": row["final_price"],
                "observed_unit_price": str(unit_price.quantize(Decimal("0.01"))),
            }
        )

    artifact = {
        "artifact_type": "demo_valuation_model",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "training_mode": "seed_price_baseline",
        "warning": "This is a tiny seed-data baseline, not a production valuation model or real market performance claim.",
        "category_unit_prices": category_unit_prices,
        "transaction_examples": transaction_examples,
        "sklearn_gradient_boosting_status": sklearn_status,
    }

    JSON_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"wrote {JSON_OUTPUT_PATH}")


def try_train_sklearn(price_rows: list[dict[str, str]]) -> str:
    try:
        import pandas as pd
        from sklearn.compose import ColumnTransformer
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder
    except ImportError:
        return "skipped: scikit-learn or pandas is not installed"

    if len(price_rows) < 4:
        return "skipped: not enough rows for a useful GradientBoostingRegressor"

    categories = sorted({row["material_category"] for row in price_rows})
    category_to_index = {category: index for index, category in enumerate(categories)}
    x_rows = pd.DataFrame([
        {
            "material_category": row["material_category"],
            "sub_category": row["sub_category"],
            "category_index": category_to_index[row["material_category"]],
        }
        for row in price_rows
    ])
    y_values = [float(row["buying_price"]) for row in price_rows]

    model = Pipeline(
        steps=[
            (
                "features",
                ColumnTransformer(
                    transformers=[
                        ("category", OneHotEncoder(handle_unknown="ignore"), ["material_category", "sub_category"]),
                    ],
                    remainder="drop",
                ),
            ),
            ("regressor", GradientBoostingRegressor(random_state=42)),
        ]
    )
    model.fit(x_rows, y_values)
    with SKLEARN_OUTPUT_PATH.open("wb") as handle:
        pickle.dump(model, handle)
    return f"trained demo GradientBoostingRegressor and wrote {SKLEARN_OUTPUT_PATH}"


def main() -> None:
    price_rows = read_rows(SEED_PRICES_PATH)
    transaction_rows = read_rows(SEED_TRANSACTIONS_PATH)
    sklearn_status = try_train_sklearn(price_rows)
    write_json_baseline(price_rows, transaction_rows, sklearn_status)
    print(sklearn_status)


if __name__ == "__main__":
    main()
