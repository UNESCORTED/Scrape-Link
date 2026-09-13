import csv
import json
import os
from pathlib import Path

import psycopg


ROOT_DIR = Path(__file__).resolve().parents[2]
DATASETS_DIR = ROOT_DIR / "datasets"


def database_url() -> str:
    return os.getenv(
        "DATABASE_URL_SYNC",
        os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://ewaste_user:change_me_local_only@localhost:5432/ewaste_platform",
        ).replace("+asyncpg", "+psycopg"),
    )


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATASETS_DIR / name).open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def point_sql(latitude: str, longitude: str) -> str:
    return f"SRID=4326;POINT({longitude} {latitude})"


def seed_recyclers(cursor: psycopg.Cursor) -> None:
    for row in read_csv("seed_recyclers.csv"):
        cursor.execute(
            """
            INSERT INTO recyclers (
                recycler_id, name, facility_location, service_area_radius_km,
                materials_accepted, authorization_id, authorization_status,
                contact_phone, offered_rates, pickup_available
            )
            VALUES (
                %(recycler_id)s, %(name)s, ST_GeogFromText(%(facility_location)s),
                %(service_area_radius_km)s, %(materials_accepted)s, %(authorization_id)s,
                %(authorization_status)s, %(contact_phone)s, %(offered_rates)s::jsonb,
                %(pickup_available)s
            )
            ON CONFLICT (recycler_id) DO NOTHING
            """,
            {
                **row,
                "facility_location": point_sql(row["latitude"], row["longitude"]),
                "materials_accepted": row["materials_accepted"].split("|"),
                "offered_rates": json.dumps(json.loads(row["offered_rates"])),
                "pickup_available": row["pickup_available"].lower() == "true",
            },
        )


def seed_prices(cursor: psycopg.Cursor) -> None:
    for row in read_csv("seed_prices.csv"):
        cursor.execute(
            """
            INSERT INTO price_history (
                material_category, sub_category, location, recorded_date,
                buying_price, market_range_min, market_range_max, unit, recycler_id, source
            )
            VALUES (
                %(material_category)s, %(sub_category)s, ST_GeogFromText(%(location)s),
                %(recorded_date)s, %(buying_price)s, %(market_range_min)s,
                %(market_range_max)s, %(unit)s, %(recycler_id)s, %(source)s
            )
            """,
            {**row, "location": point_sql(row["latitude"], row["longitude"])},
        )


def seed_transactions(cursor: psycopg.Cursor) -> None:
    for row in read_csv("seed_transactions.csv"):
        cursor.execute(
            """
            INSERT INTO collectors (phone_number_hash, preferred_language, operating_area)
            VALUES (%(collector_phone_number_hash)s, %(collector_preferred_language)s, ST_GeogFromText(%(location)s))
            ON CONFLICT (phone_number_hash) DO UPDATE
            SET preferred_language = EXCLUDED.preferred_language
            RETURNING collector_id
            """,
            {
                "collector_phone_number_hash": row["collector_phone_number_hash"],
                "collector_preferred_language": row["collector_preferred_language"],
                "location": point_sql(row["latitude"], row["longitude"]),
            },
        )
        collector_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO material_lots (
                lot_id, collector_id, material_category, sub_category, approx_weight_kg,
                quoted_price, final_sale_value, collection_location, collection_timestamp,
                status, sync_status
            )
            VALUES (
                %(lot_id)s, %(collector_id)s, %(material_category)s, %(sub_category)s,
                %(approx_weight_kg)s, %(quoted_price)s, %(final_price)s,
                ST_GeogFromText(%(location)s), %(collection_timestamp)s,
                'completed', 'synced'
            )
            ON CONFLICT (lot_id) DO NOTHING
            """,
            {**row, "collector_id": collector_id, "location": point_sql(row["latitude"], row["longitude"])},
        )

        cursor.execute(
            """
            INSERT INTO transactions (
                transaction_id, lot_id, collector_id, recycler_id, quoted_price,
                final_price, payment_mode, payment_status, transaction_status,
                handover_location, handover_timestamp
            )
            VALUES (
                %(transaction_id)s, %(lot_id)s, %(collector_id)s, %(recycler_id)s,
                %(quoted_price)s, %(final_price)s, %(payment_mode)s,
                %(payment_status)s, %(transaction_status)s,
                ST_GeogFromText(%(location)s), %(handover_timestamp)s
            )
            ON CONFLICT (transaction_id) DO NOTHING
            """,
            {**row, "collector_id": collector_id, "location": point_sql(row["latitude"], row["longitude"])},
        )


def seed_traceability(cursor: psycopg.Cursor) -> None:
    for row in read_csv("seed_traceability.csv"):
        cursor.execute(
            """
            INSERT INTO traceability_records (
                trace_id, lot_id, photo_refs, weight_kg, gps_location, captured_at,
                handover_reference_number, recycler_confirmed, recycler_confirmed_at, status_history
            )
            VALUES (
                %(trace_id)s, %(lot_id)s, %(photo_refs)s, %(weight_kg)s,
                ST_GeogFromText(%(gps_location)s), %(captured_at)s,
                %(handover_reference_number)s, %(recycler_confirmed)s,
                %(recycler_confirmed_at)s, %(status_history)s::jsonb
            )
            ON CONFLICT (handover_reference_number) DO NOTHING
            """,
            {
                **row,
                "photo_refs": row["photo_refs"].split("|"),
                "gps_location": point_sql(row["latitude"], row["longitude"]),
                "recycler_confirmed": row["recycler_confirmed"].lower() == "true",
                "status_history": json.dumps(json.loads(row["status_history"])),
            },
        )


def seed_earnings_ledger(cursor: psycopg.Cursor) -> None:
    cursor.execute(
        """
        INSERT INTO earnings_ledger (collector_id, transaction_id, amount, entry_type)
        SELECT collector_id, transaction_id, final_price, 'earned'
        FROM transactions
        WHERE final_price IS NOT NULL
        AND NOT EXISTS (
            SELECT 1
            FROM earnings_ledger
            WHERE earnings_ledger.transaction_id = transactions.transaction_id
            AND earnings_ledger.entry_type = 'earned'
        )
        """
    )


def main() -> None:
    with psycopg.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            seed_recyclers(cursor)
            seed_prices(cursor)
            seed_transactions(cursor)
            seed_traceability(cursor)
            seed_earnings_ledger(cursor)
        connection.commit()


if __name__ == "__main__":
    main()
