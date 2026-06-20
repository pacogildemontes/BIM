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
    category    TEXT    NOT NULL DEFAULT 'otro',     -- seguro | ibi | irpf | iva | impuesto | suministro | hipoteca | otro
    amount      REAL,
    due_date    TEXT    NOT NULL,                    -- ISO YYYY-MM-DD del próximo vencimiento
    recurrence  TEXT    NOT NULL DEFAULT 'unica',    -- unica | mensual | trimestral | semestral | anual
    account_id  INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    paid        INTEGER NOT NULL DEFAULT 0,          -- 1 si el vencimiento actual ya está pagado
    notes       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_obl_due ON obligations(due_date);
