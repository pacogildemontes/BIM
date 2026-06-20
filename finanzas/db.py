"""Acceso a la base de datos SQLite del hub de finanzas."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = PACKAGE_DIR / "schema.sql"


def default_db_path() -> str:
    """Ruta del fichero de base de datos (configurable con la variable FINANCE_DB)."""
    return os.environ.get("FINANCE_DB", str(PACKAGE_DIR.parent / "finanzas.db"))


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or default_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | None = None) -> None:
    """Crea las tablas si no existen y aplica migraciones ligeras."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _migrate(conn)
        conn.commit()
    finally:
        conn.close()


def _columns(conn, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def _migrate(conn) -> None:
    """Añade columnas nuevas a bases de datos creadas con versiones anteriores."""
    if "property_id" not in _columns(conn, "obligations"):
        conn.execute("ALTER TABLE obligations ADD COLUMN property_id INTEGER REFERENCES properties(id)")
