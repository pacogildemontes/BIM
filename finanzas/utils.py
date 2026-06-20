"""Utilidades de parseo y formato (importes, fechas) tolerantes a formatos españoles."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d/%m/%y",
    "%d.%m.%Y",
    "%Y/%m/%d",
)


def parse_amount(raw) -> Optional[float]:
    """Convierte un importe en texto a float.

    Acepta formato español (1.234,56), inglés (1,234.56), símbolos de divisa,
    paréntesis para negativos y signos. Devuelve None si no puede parsear.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)

    text = str(raw).strip()
    if not text:
        return None

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]

    # Quitar todo lo que no sea dígito, separador o signo.
    text = re.sub(r"[^\d,.\-+]", "", text)
    if not text or text in {"-", "+"}:
        return None

    if "," in text and "." in text:
        # El último separador que aparece es el decimal.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        # Coma como decimal (formato español).
        text = text.replace(".", "").replace(",", ".")

    try:
        value = float(text)
    except ValueError:
        return None
    return -value if negative else value


def parse_date(raw) -> Optional[str]:
    """Devuelve la fecha en ISO (YYYY-MM-DD) o None."""
    if raw is None:
        return None
    if isinstance(raw, (datetime, date)):
        return raw.strftime("%Y-%m-%d")

    text = str(raw).strip()
    if not text:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def format_eur(value, currency: str = "EUR") -> str:
    """Formatea un importe al estilo español: 1.234,56 €."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    symbol = "€" if currency == "EUR" else currency
    return f"{formatted} {symbol}"
