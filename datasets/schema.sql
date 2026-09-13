CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE collectors (
    collector_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number_hash TEXT UNIQUE NOT NULL,
    preferred_language TEXT CHECK (preferred_language IN ('hi','mr','en')) DEFAULT 'hi',
    operating_area GEOGRAPHY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE recyclers (
    recycler_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    facility_location GEOGRAPHY(Point, 4326) NOT NULL,
    service_area_radius_km NUMERIC DEFAULT 15,
    materials_accepted TEXT[] NOT NULL,
    authorization_id TEXT,
    authorization_status TEXT CHECK (authorization_status IN ('authorized','pending','unverified','suspended')),
    contact_phone TEXT,
    offered_rates JSONB,
    pickup_available BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_recyclers_location ON recyclers USING GIST (facility_location);

CREATE TABLE material_lots (
    lot_id UUID PRIMARY KEY,
    collector_id UUID REFERENCES collectors(collector_id),
    material_category TEXT NOT NULL,
    sub_category TEXT,
    description TEXT,
    image_ref TEXT,
    approx_weight_kg NUMERIC NOT NULL,
    condition TEXT,
    source_type TEXT,
    estimated_value NUMERIC,
    quoted_price NUMERIC,
    final_sale_value NUMERIC,
    collection_location GEOGRAPHY(Point, 4326),
    collection_timestamp TIMESTAMPTZ,
    status TEXT CHECK (status IN ('draft','listed','matched','handed_over','completed','disputed')) DEFAULT 'draft',
    sync_status TEXT CHECK (sync_status IN ('pending','synced','conflict')) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE price_history (
    price_id BIGSERIAL PRIMARY KEY,
    material_category TEXT NOT NULL,
    sub_category TEXT,
    location GEOGRAPHY(Point, 4326),
    recorded_date DATE NOT NULL,
    buying_price NUMERIC NOT NULL,
    market_range_min NUMERIC,
    market_range_max NUMERIC,
    unit TEXT DEFAULT 'kg',
    recycler_id UUID REFERENCES recyclers(recycler_id),
    source TEXT
);
CREATE INDEX idx_price_category_date ON price_history (material_category, recorded_date);

CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lot_id UUID REFERENCES material_lots(lot_id),
    collector_id UUID REFERENCES collectors(collector_id),
    recycler_id UUID REFERENCES recyclers(recycler_id),
    quoted_price NUMERIC,
    final_price NUMERIC,
    payment_mode TEXT CHECK (payment_mode IN ('cash','digital')) DEFAULT 'cash',
    payment_status TEXT CHECK (payment_status IN ('pending','paid','partial')) DEFAULT 'pending',
    transaction_status TEXT CHECK (transaction_status IN ('initiated','handed_over','confirmed','completed','flagged')) DEFAULT 'initiated',
    handover_location GEOGRAPHY(Point, 4326),
    handover_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE traceability_records (
    trace_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lot_id UUID REFERENCES material_lots(lot_id),
    photo_refs TEXT[],
    weight_kg NUMERIC,
    gps_location GEOGRAPHY(Point, 4326),
    captured_at TIMESTAMPTZ,
    handover_reference_number TEXT UNIQUE NOT NULL,
    recycler_confirmed BOOLEAN DEFAULT false,
    recycler_confirmed_at TIMESTAMPTZ,
    status_history JSONB DEFAULT '[]'
);

CREATE TABLE earnings_ledger (
    entry_id BIGSERIAL PRIMARY KEY,
    collector_id UUID REFERENCES collectors(collector_id),
    transaction_id UUID REFERENCES transactions(transaction_id),
    amount NUMERIC NOT NULL,
    entry_type TEXT CHECK (entry_type IN ('earned','paid','pending_due')),
    created_at TIMESTAMPTZ DEFAULT now()
);

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
    ON tx.lot_id = ml.lot_id;
