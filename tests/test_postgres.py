"""Pruebas del backend PostgreSQL.

Solo se ejecutan si la variable de entorno DATABASE_URL apunta a un Postgres
(p. ej. en local con un servidor de pruebas, o contra Supabase). En CI sin
Postgres, se omiten automáticamente.
"""
import os

import pytest

DATABASE_URL = os.environ.get("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL.startswith(("postgres://", "postgresql://")),
    reason="DATABASE_URL no apunta a PostgreSQL",
)


@pytest.fixture
def client():
    from finanzas import create_app
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_full_flow_on_postgres(client):
    assert client.get("/").status_code == 200

    # Cuenta + movimiento (verifica lastrowid emulado y ajuste de saldo).
    client.post("/cuentas/nueva", data={"name": "Banco PG", "balance": "1000"},
                follow_redirects=True)
    client.post("/cuentas/1/movimiento", data={
        "date": "2026-06-10", "description": "Compra", "amount": "-50",
    }, follow_redirects=True)
    assert b"950,00" in client.get("/cuentas/1").data

    # Vivienda con gasto recurrente y rentabilidad.
    client.post("/viviendas/nueva", data={
        "name": "Piso PG", "value": "200000", "mortgage": "50000",
        "rented": "on", "monthly_rent": "1000",
    }, follow_redirects=True)
    client.post("/calendario/nueva", data={
        "name": "Luz", "category": "suministro", "amount": "50",
        "due_date": "2026-07-01", "recurrence": "mensual", "property_id": "1",
    }, follow_redirects=True)
    assert b"11.400,00" in client.get("/viviendas/1").data

    # Inversión + proyección.
    client.post("/inversiones/nueva", data={
        "name": "VWCE", "units": "100", "avg_cost": "100", "current_price": "120",
        "target_pct": "100",
    }, follow_redirects=True)
    assert b"12.000,00" in client.get("/inversiones").data

    # Recurrencia trimestral: al marcar pagado, la fecha avanza un trimestre.
    # (la obligación "Luz" anterior es id=1, esta IVA es id=2)
    client.post("/calendario/nueva", data={
        "name": "IVA", "category": "iva", "amount": "300",
        "due_date": "2026-04-20", "recurrence": "trimestral",
    }, follow_redirects=True)
    client.post("/calendario/2/pagado", follow_redirects=True)
    page = client.get("/calendario")
    assert b"2026-07-20" in page.data
