-- Esquema PostgreSQL (Supabase u otro Postgres) del hub de finanzas.
-- Equivalente a schema.sql pero con tipos/dialecto de Postgres.
-- El orden respeta las claves foráneas (Postgres exige que la tabla referenciada exista).

CREATE TABLE IF NOT EXISTS accounts (
    id          SERIAL  PRIMARY KEY,
    name        TEXT    NOT NULL,
    institution TEXT,
    type        TEXT    NOT NULL DEFAULT 'banco',
    currency    TEXT    NOT NULL DEFAULT 'EUR',
    balance     DOUBLE PRECISION NOT NULL DEFAULT 0,
    notes       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (now()::text)
);

CREATE TABLE IF NOT EXISTS properties (
    id             SERIAL  PRIMARY KEY,
    name           TEXT    NOT NULL,
    address        TEXT,
    type           TEXT    NOT NULL DEFAULT 'vivienda',
    value          DOUBLE PRECISION NOT NULL DEFAULT 0,
    mortgage       DOUBLE PRECISION NOT NULL DEFAULT 0,
    purchase_price DOUBLE PRECISION,
    rented         INTEGER NOT NULL DEFAULT 0,
    monthly_rent   DOUBLE PRECISION,
    tenant         TEXT,
    notes          TEXT,
    created_at     TEXT    NOT NULL DEFAULT (now()::text)
);

CREATE TABLE IF NOT EXISTS transactions (
    id          SERIAL  PRIMARY KEY,
    account_id  INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    date        TEXT    NOT NULL,
    description TEXT,
    category    TEXT,
    amount      DOUBLE PRECISION NOT NULL,
    source      TEXT    NOT NULL DEFAULT 'manual',
    created_at  TEXT    NOT NULL DEFAULT (now()::text)
);

CREATE INDEX IF NOT EXISTS idx_tx_account ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_tx_date    ON transactions(date);

CREATE TABLE IF NOT EXISTS assets (
    id          SERIAL  PRIMARY KEY,
    name        TEXT    NOT NULL,
    type        TEXT    NOT NULL DEFAULT 'propiedad',
    value       DOUBLE PRECISION NOT NULL DEFAULT 0,
    liability   DOUBLE PRECISION NOT NULL DEFAULT 0,
    notes       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (now()::text)
);

CREATE TABLE IF NOT EXISTS obligations (
    id          SERIAL  PRIMARY KEY,
    name        TEXT    NOT NULL,
    category    TEXT    NOT NULL DEFAULT 'otro',
    amount      DOUBLE PRECISION,
    due_date    TEXT    NOT NULL,
    recurrence  TEXT    NOT NULL DEFAULT 'unica',
    account_id  INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    property_id INTEGER REFERENCES properties(id) ON DELETE SET NULL,
    paid        INTEGER NOT NULL DEFAULT 0,
    notes       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (now()::text)
);

-- Migración para bases Postgres anteriores sin la columna property_id.
ALTER TABLE obligations ADD COLUMN IF NOT EXISTS property_id INTEGER REFERENCES properties(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_obl_due      ON obligations(due_date);
CREATE INDEX IF NOT EXISTS idx_obl_property ON obligations(property_id);

CREATE TABLE IF NOT EXISTS holdings (
    id            SERIAL  PRIMARY KEY,
    ticker        TEXT,
    name          TEXT    NOT NULL,
    category      TEXT,
    units         DOUBLE PRECISION NOT NULL DEFAULT 0,
    avg_cost      DOUBLE PRECISION NOT NULL DEFAULT 0,
    current_price DOUBLE PRECISION,
    target_pct    DOUBLE PRECISION,
    notes         TEXT,
    created_at    TEXT    NOT NULL DEFAULT (now()::text)
);

CREATE TABLE IF NOT EXISTS investment_plan (
    id                   INTEGER PRIMARY KEY CHECK (id = 1),
    monthly_contribution DOUBLE PRECISION NOT NULL DEFAULT 0,
    expected_return      DOUBLE PRECISION NOT NULL DEFAULT 5,
    notes                TEXT
);
INSERT INTO investment_plan (id, monthly_contribution, expected_return)
VALUES (1, 0, 5) ON CONFLICT (id) DO NOTHING;
