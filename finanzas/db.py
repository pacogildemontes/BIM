"""Acceso a la base de datos del hub de finanzas.

Soporta dos backends de forma transparente:

* **SQLite** (por defecto, para uso local) — fichero indicado por ``FINANCE_DB``.
* **PostgreSQL** (p. ej. Supabase, para despliegue con datos persistentes) — se
  activa definiendo la variable de entorno ``DATABASE_URL``.

Los modelos usan SQL con marcador ``?`` y ``cursor.lastrowid``; el adaptador de
Postgres traduce los marcadores a ``%s`` y emula ``lastrowid`` con ``RETURNING id``,
de modo que ``models.py`` no necesita conocer el backend.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
SCHEMA_SQLITE = PACKAGE_DIR / "schema.sql"
SCHEMA_POSTGRES = PACKAGE_DIR / "schema_postgres.sql"


def database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


def is_postgres() -> bool:
    url = database_url()
    return bool(url) and url.startswith(("postgres://", "postgresql://"))


def default_db_path() -> str:
    """Ruta del fichero SQLite (configurable con la variable FINANCE_DB)."""
    return os.environ.get("FINANCE_DB", str(PACKAGE_DIR.parent / "finanzas.db"))


# --- Adaptador PostgreSQL ----------------------------------------------------

class _PgResult:
    """Envuelve un cursor de psycopg2 imitando la API de sqlite3 que usan los modelos."""

    def __init__(self, cursor, lastrowid):
        self._cursor = cursor
        self.lastrowid = lastrowid

    def fetchone(self):
        try:
            return self._cursor.fetchone()
        except Exception:  # noqa: BLE001 - statements sin resultado (INSERT/UPDATE)
            return None

    def fetchall(self):
        try:
            return self._cursor.fetchall()
        except Exception:  # noqa: BLE001
            return []


class _PgConnection:
    """Conexión a Postgres con la misma interfaz que usamos sobre sqlite3."""

    def __init__(self, dsn: str):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        self._conn = psycopg2.connect(dsn)
        self._conn.set_client_encoding("UTF8")
        self._factory = RealDictCursor

    def execute(self, sql: str, params=()):
        query = sql.replace("?", "%s")
        stripped = query.lstrip().lower()
        returning = False
        if stripped.startswith("insert into") and "returning" not in stripped:
            query = query.rstrip().rstrip(";") + " RETURNING id"
            returning = True
        cursor = self._conn.cursor(cursor_factory=self._factory)
        cursor.execute(query, params)
        lastrowid = None
        if returning:
            row = cursor.fetchone()
            lastrowid = row["id"] if row else None
        return _PgResult(cursor, lastrowid)

    def executescript(self, script: str):
        with self._conn.cursor() as cursor:
            cursor.execute(script)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


# --- API pública -------------------------------------------------------------

def get_connection(db_path: str | None = None):
    if is_postgres():
        return _PgConnection(database_url())
    conn = sqlite3.connect(db_path or default_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | None = None) -> None:
    """Crea las tablas si no existen y aplica migraciones ligeras."""
    conn = get_connection(db_path)
    try:
        if is_postgres():
            conn.executescript(SCHEMA_POSTGRES.read_text(encoding="utf-8"))
        else:
            conn.executescript(SCHEMA_SQLITE.read_text(encoding="utf-8"))
            _migrate_sqlite(conn)
        conn.commit()
    finally:
        conn.close()


def _columns(conn, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def _migrate_sqlite(conn) -> None:
    """Añade columnas nuevas a bases SQLite creadas con versiones anteriores."""
    if "property_id" not in _columns(conn, "obligations"):
        conn.execute("ALTER TABLE obligations ADD COLUMN property_id INTEGER REFERENCES properties(id)")
