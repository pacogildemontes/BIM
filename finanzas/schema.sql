-- Esquema de la base de datos del hub de finanzas personales.
-- Todas las cantidades se guardan en la divisa de la cuenta/activo (por defecto EUR).

CREATE TABLE IF NOT EXISTS accounts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    institution TEXT,
    type        TEXT    NOT NULL DEFAULT 'banco',   -- banco | tarjeta | inversion | efectivo
    currency    TEXT    NOT NULL DEFAULT 'EUR',
    balance     REAL    NOT NULL DEFAULT 0,          -- saldo actual
    notes       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id  INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    date        TEXT    NOT NULL,                    -- ISO YYYY-MM-DD
    description TEXT,
    category    TEXT,
    amount      REAL    NOT NULL,                    -- positivo ingreso, negativo gasto
    source      TEXT    NOT NULL DEFAULT 'manual',   -- manual | import
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tx_account ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_tx_date    ON transactions(date);

CREATE TABLE IF NOT EXISTS assets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    type        TEXT    NOT NULL DEFAULT 'propiedad',-- propiedad | fondo | inversion | otro
    value       REAL    NOT NULL DEFAULT 0,          -- valor de mercado estimado
    liability   REAL    NOT NULL DEFAULT 0,          -- deuda asociada (p.ej. hipoteca)
    notes       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS obligations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    category    TEXT    NOT NULL DEFAULT 'otro',     -- seguro | ibi | irpf | iva | impuesto | suministro | hipoteca | comunidad | otro
    amount      REAL,
    due_date    TEXT    NOT NULL,                    -- ISO YYYY-MM-DD del próximo vencimiento
    recurrence  TEXT    NOT NULL DEFAULT 'unica',    -- unica | mensual | bimestral | trimestral | semestral | anual
    account_id  INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    property_id INTEGER REFERENCES properties(id) ON DELETE SET NULL,
    paid        INTEGER NOT NULL DEFAULT 0,          -- 1 si el vencimiento actual ya está pagado
    notes       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_obl_due      ON obligations(due_date);
CREATE INDEX IF NOT EXISTS idx_obl_property ON obligations(property_id);

-- Viviendas / inmuebles, cada uno con su ficha de gastos e ingresos por alquiler.
CREATE TABLE IF NOT EXISTS properties (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    address        TEXT,
    type           TEXT    NOT NULL DEFAULT 'vivienda', -- vivienda | local | garaje | terreno | otro
    value          REAL    NOT NULL DEFAULT 0,          -- valor de mercado estimado
    mortgage       REAL    NOT NULL DEFAULT 0,          -- deuda hipotecaria pendiente
    purchase_price REAL,
    rented         INTEGER NOT NULL DEFAULT 0,          -- 1 si está alquilada
    monthly_rent   REAL,                                -- ingreso mensual por alquiler
    tenant         TEXT,                                -- inquilino
    notes          TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Cartera de inversión (ETFs/fondos): se replica el plan y se simula su valor.
CREATE TABLE IF NOT EXISTS holdings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker        TEXT,
    name          TEXT    NOT NULL,
    category      TEXT,                                 -- RV global, bonos, etc.
    units         REAL    NOT NULL DEFAULT 0,           -- participaciones
    avg_cost      REAL    NOT NULL DEFAULT 0,           -- coste medio por participación
    current_price REAL,                                 -- último precio conocido (manual)
    target_pct    REAL,                                 -- % objetivo dentro del plan
    notes         TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Parámetros globales del plan de inversión (una sola fila).
CREATE TABLE IF NOT EXISTS investment_plan (
    id                   INTEGER PRIMARY KEY CHECK (id = 1),
    monthly_contribution REAL    NOT NULL DEFAULT 0,    -- aportación mensual
    expected_return      REAL    NOT NULL DEFAULT 5,    -- % rentabilidad anual esperada
    notes                TEXT
);
INSERT OR IGNORE INTO investment_plan (id, monthly_contribution, expected_return) VALUES (1, 0, 5);
