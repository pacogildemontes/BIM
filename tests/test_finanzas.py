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
