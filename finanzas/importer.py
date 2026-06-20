"""Importación de extractos bancarios en CSV.

Detecta automáticamente las columnas habituales (fecha, concepto, importe) en
extractos españoles e ingleses. Si el CSV separa cargos y abonos en dos
columnas (Debe / Haber), también lo resuelve.
"""
from __future__ import annotations

import csv
import io
from typing import Iterable

from .utils import parse_amount, parse_date

DATE_KEYS = {"fecha", "fecha operacion", "fecha valor", "date", "fecha contable"}
DESC_KEYS = {"concepto", "descripcion", "descripción", "description", "detalle", "movimiento", "concept"}
AMOUNT_KEYS = {"importe", "amount", "cantidad", "valor", "monto"}
DEBIT_KEYS = {"debe", "cargo", "gasto", "debit", "salida"}
CREDIT_KEYS = {"haber", "abono", "ingreso", "credit", "entrada"}


def _norm(header: str) -> str:
    return (header or "").strip().lower()


def _match(headers, candidates):
    for h in headers:
        if _norm(h) in candidates:
            return h
    return None


def parse_csv(content: str) -> list[dict]:
    """Devuelve una lista de movimientos {date, description, amount}.

    Lanza ValueError con un mensaje claro si no encuentra columnas reconocibles.
    """
    # Detectar el delimitador (coma, punto y coma o tabulador).
    sample = content[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";" if sample.count(";") >= sample.count(",") else ","

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    headers = reader.fieldnames or []
    if not headers:
        raise ValueError("El CSV no tiene cabecera de columnas.")

    date_col = _match(headers, DATE_KEYS)
    desc_col = _match(headers, DESC_KEYS)
    amount_col = _match(headers, AMOUNT_KEYS)
    debit_col = _match(headers, DEBIT_KEYS)
    credit_col = _match(headers, CREDIT_KEYS)

    if not date_col:
        raise ValueError(
            f"No se encontró una columna de fecha. Cabeceras detectadas: {', '.join(headers)}"
        )
    if not amount_col and not (debit_col or credit_col):
        raise ValueError(
            f"No se encontró columna de importe. Cabeceras detectadas: {', '.join(headers)}"
        )

    movements: list[dict] = []
    for row in reader:
        iso_date = parse_date(row.get(date_col))
        if not iso_date:
            continue

        if amount_col:
            amount = parse_amount(row.get(amount_col))
        else:
            debit = parse_amount(row.get(debit_col)) if debit_col else None
            credit = parse_amount(row.get(credit_col)) if credit_col else None
            amount = (credit or 0) - abs(debit) if debit else (credit or 0)
        if amount is None:
            continue

        description = (row.get(desc_col) or "").strip() if desc_col else ""
        movements.append({
            "date": iso_date,
            "description": description,
            "amount": amount,
        })

    if not movements:
        raise ValueError("No se pudo extraer ningún movimiento válido del archivo.")
    return movements
