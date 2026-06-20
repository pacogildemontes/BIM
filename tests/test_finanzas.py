"""Pruebas de humo del hub de finanzas."""
import os
import tempfile

import pytest

from finanzas import create_app
from finanzas.importer import parse_csv
from finanzas.utils import format_eur, parse_amount, parse_date


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app = create_app(db_path=path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    os.unlink(path)


def test_parse_amount_spanish():
    assert parse_amount("1.234,56") == 1234.56
    assert parse_amount("-64,30") == -64.30
    assert parse_amount("(32,10)") == -32.10
    assert parse_amount("1,234.56") == 1234.56
    assert parse_amount("") is None


def test_parse_date_formats():
    assert parse_date("01/06/2026") == "2026-06-01"
    assert parse_date("2026-06-01") == "2026-06-01"
    assert parse_date("no es fecha") is None


def test_format_eur():
    assert format_eur(1234.5) == "1.234,50 €"


def test_parse_csv_semicolon():
    content = "Fecha;Concepto;Importe\n01/06/2026;Nomina;1.850,00\n03/06/2026;Super;-64,30\n"
    movements = parse_csv(content)
    assert len(movements) == 2
    assert movements[0]["amount"] == 1850.0
    assert movements[1]["amount"] == -64.30


def test_dashboard_and_account_flow(client):
    assert client.get("/").status_code == 200

    # Crear cuenta
    resp = client.post("/cuentas/nueva", data={
        "name": "Nómina", "institution": "BBVA", "type": "banco",
        "currency": "EUR", "balance": "1000",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert "Nómina".encode() in resp.data

    # Añadir movimiento ajusta el saldo
    client.post("/cuentas/1/movimiento", data={
        "date": "2026-06-10", "description": "Compra", "amount": "-50",
    }, follow_redirects=True)
    detail = client.get("/cuentas/1")
    assert b"950,00" in detail.data


def test_obligation_recurrence_advances(client):
    client.post("/cuentas/nueva", data={"name": "C", "balance": "0"})
    client.post("/calendario/nueva", data={
        "name": "IVA", "category": "iva", "amount": "300",
        "due_date": "2026-04-20", "recurrence": "trimestral",
    }, follow_redirects=True)
    client.post("/calendario/1/pagado", follow_redirects=True)
    page = client.get("/calendario")
    assert b"2026-07-20" in page.data  # avanzó un trimestre


def test_property_with_expenses_and_yield(client):
    resp = client.post("/viviendas/nueva", data={
        "name": "Piso Centro", "type": "vivienda", "value": "200000",
        "mortgage": "50000", "rented": "on", "monthly_rent": "1000",
    }, follow_redirects=True)
    assert "Piso Centro".encode() in resp.data

    # Gasto recurrente ligado a la vivienda (luz mensual de 50 €/mes = 600/año).
    client.post("/calendario/nueva", data={
        "name": "Luz", "category": "suministro", "amount": "50",
        "due_date": "2026-07-01", "recurrence": "mensual", "property_id": "1",
    }, follow_redirects=True)
    ficha = client.get("/viviendas/1")
    assert ficha.status_code == 200
    assert b"Luz" in ficha.data
    # Alquiler anual 12000 - gastos 600 = 11400 neto.
    assert b"11.400,00" in ficha.data


def test_portfolio_value_and_projection(client):
    client.post("/inversiones/nueva", data={
        "ticker": "vwce", "name": "Vanguard FTSE All-World", "units": "100",
        "avg_cost": "100", "current_price": "120", "target_pct": "100",
    }, follow_redirects=True)
    client.post("/inversiones/plan", data={
        "monthly_contribution": "500", "expected_return": "7",
    }, follow_redirects=True)
    page = client.get("/inversiones")
    assert page.status_code == 200
    assert b"12.000,00" in page.data  # valor actual 100 * 120

    from finanzas import models
    proj = models.project_portfolio(12000, 500, 7, years=10)
    assert proj[-1]["value"] > proj[0]["value"]


def test_net_worth_aggregates_everything(client):
    from finanzas import models
    from finanzas.db import get_connection
    client.post("/cuentas/nueva", data={"name": "Banco", "balance": "10000"})
    client.post("/viviendas/nueva", data={"name": "Casa", "value": "200000", "mortgage": "120000"})
    client.post("/inversiones/nueva", data={
        "name": "ETF", "units": "10", "avg_cost": "100", "current_price": "150"})
    conn = get_connection(client.application.config["DB_PATH"])
    s = models.net_worth_summary(conn)
    conn.close()
    # 10000 + (200000-120000) + (10*150) = 91500
    assert round(s["net_worth"], 2) == 91500.0


def test_login_gate(monkeypatch):
    import tempfile, os as _os
    monkeypatch.setenv("APP_PASSWORD", "secreto")
    fd, path = tempfile.mkstemp(suffix=".db")
    _os.close(fd)
    app = create_app(db_path=path)
    c = app.test_client()
    # Sin sesión, redirige al login.
    assert c.get("/", follow_redirects=False).status_code == 302
    # Con la contraseña correcta, entra.
    c.post("/login", data={"password": "secreto"}, follow_redirects=True)
    assert c.get("/").status_code == 200
    _os.unlink(path)
