"""Initial PostGIS schema for the e-waste platform.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "collectors",
        sa.Column("collector_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("phone_number_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("preferred_language", sa.Text(), server_default=sa.text("'hi'")),
        sa.Column("operating_area", Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("preferred_language IN ('hi','mr','en')", name="collectors_preferred_language_check"),
    )

    op.create_table(
        "recyclers",
        sa.Column("recycler_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("facility_location", Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False),
        sa.Column("service_area_radius_km", sa.Numeric(), server_default=sa.text("15")),
        sa.Column("materials_accepted", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("authorization_id", sa.Text()),
        sa.Column("authorization_status", sa.Text()),
        sa.Column("contact_phone", sa.Text()),
        sa.Column("offered_rates", postgresql.JSONB()),
        sa.Column("pickup_available", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "authorization_status IN ('authorized','pending','unverified','suspended')",
            name="recyclers_authorization_status_check",
        ),
    )
    op.create_index("idx_recyclers_location", "recyclers", ["facility_location"], postgresql_using="gist")

    op.create_table(
        "material_lots",
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("collector_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("collectors.collector_id")),
        sa.Column("material_category", sa.Text(), nullable=False),
        sa.Column("sub_category", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("image_ref", sa.Text()),
        sa.Column("approx_weight_kg", sa.Numeric(), nullable=False),
        sa.Column("condition", sa.Text()),
        sa.Column("source_type", sa.Text()),
        sa.Column("estimated_value", sa.Numeric()),
        sa.Column("quoted_price", sa.Numeric()),
        sa.Column("final_sale_value", sa.Numeric()),
        sa.Column("collection_location", Geography(geometry_type="POINT", srid=4326, spatial_index=False)),
        sa.Column("collection_timestamp", sa.DateTime(timezone=True)),
        sa.Column("status", sa.Text(), server_default=sa.text("'draft'")),
        sa.Column("sync_status", sa.Text(), server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('draft','listed','matched','handed_over','completed','disputed')",
            name="material_lots_status_check",
        ),
        sa.CheckConstraint(
            "sync_status IN ('pending','synced','conflict')",
            name="material_lots_sync_status_check",
        ),
    )

    op.create_table(
        "price_history",
        sa.Column("price_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("material_category", sa.Text(), nullable=False),
        sa.Column("sub_category", sa.Text()),
        sa.Column("location", Geography(geometry_type="POINT", srid=4326, spatial_index=False)),
        sa.Column("recorded_date", sa.Date(), nullable=False),
        sa.Column("buying_price", sa.Numeric(), nullable=False),
        sa.Column("market_range_min", sa.Numeric()),
        sa.Column("market_range_max", sa.Numeric()),
        sa.Column("unit", sa.Text(), server_default=sa.text("'kg'")),
        sa.Column("recycler_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recyclers.recycler_id")),
        sa.Column("source", sa.Text()),
    )
    op.create_index("idx_price_category_date", "price_history", ["material_category", "recorded_date"])

    op.create_table(
        "transactions",
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("material_lots.lot_id")),
        sa.Column("collector_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("collectors.collector_id")),
        sa.Column("recycler_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recyclers.recycler_id")),
        sa.Column("quoted_price", sa.Numeric()),
        sa.Column("final_price", sa.Numeric()),
        sa.Column("payment_mode", sa.Text(), server_default=sa.text("'cash'")),
        sa.Column("payment_status", sa.Text(), server_default=sa.text("'pending'")),
        sa.Column("transaction_status", sa.Text(), server_default=sa.text("'initiated'")),
        sa.Column("handover_location", Geography(geometry_type="POINT", srid=4326, spatial_index=False)),
        sa.Column("handover_timestamp", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("payment_mode IN ('cash','digital')", name="transactions_payment_mode_check"),
        sa.CheckConstraint("payment_status IN ('pending','paid','partial')", name="transactions_payment_status_check"),
        sa.CheckConstraint(
            "transaction_status IN ('initiated','handed_over','confirmed','completed','flagged')",
            name="transactions_transaction_status_check",
        ),
    )

    op.create_table(
        "traceability_records",
        sa.Column("trace_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("material_lots.lot_id")),
        sa.Column("photo_refs", postgresql.ARRAY(sa.Text())),
        sa.Column("weight_kg", sa.Numeric()),
        sa.Column("gps_location", Geography(geometry_type="POINT", srid=4326, spatial_index=False)),
        sa.Column("captured_at", sa.DateTime(timezone=True)),
        sa.Column("handover_reference_number", sa.Text(), nullable=False, unique=True),
        sa.Column("recycler_confirmed", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("recycler_confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("status_history", postgresql.JSONB(), server_default=sa.text("'[]'")),
    )

    op.create_table(
        "earnings_ledger",
        sa.Column("entry_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("collector_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("collectors.collector_id")),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transactions.transaction_id")),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("entry_type", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("entry_type IN ('earned','paid','pending_due')", name="earnings_ledger_entry_type_check"),
    )

    op.execute(
        """
        CREATE VIEW ml_training_view AS
        SELECT
            ml.lot_id,
            ml.collector_id,
            ml.material_category,
            ml.sub_category,
            ml.approx_weight_kg,
            ml.condition,
            ml.source_type,
            ml.estimated_value,
            ml.quoted_price,
            ml.final_sale_value,
            ml.collection_location,
            ml.collection_timestamp,
            ph.recorded_date AS price_recorded_date,
            ph.buying_price,
            ph.market_range_min,
            ph.market_range_max,
            ph.unit,
            ph.source AS price_source,
            tx.transaction_id,
            tx.recycler_id,
            tx.final_price,
            tx.payment_mode,
            tx.payment_status,
            tx.transaction_status
        FROM material_lots ml
        LEFT JOIN price_history ph
            ON ph.material_category = ml.material_category
            AND (ph.sub_category = ml.sub_category OR ph.sub_category IS NULL OR ml.sub_category IS NULL)
        LEFT JOIN transactions tx
            ON tx.lot_id = ml.lot_id
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS ml_training_view")
    op.drop_table("earnings_ledger")
    op.drop_table("traceability_records")
    op.drop_table("transactions")
    op.drop_index("idx_price_category_date", table_name="price_history")
    op.drop_table("price_history")
    op.drop_table("material_lots")
    op.drop_index("idx_recyclers_location", table_name="recyclers")
    op.drop_table("recyclers")
    op.drop_table("collectors")
