"""Funciones de acceso a datos sobre la conexión SQLite."""
from __future__ import annotations

from datetime import date, datetime, timedelta

# --- Cuentas -----------------------------------------------------------------

def list_accounts(db):
    return db.execute("SELECT * FROM accounts ORDER BY name").fetchall()


def get_account(db, account_id):
    return db.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()


def create_account(db, name, institution, type_, currency, balance, notes):
    cur = db.execute(
        "INSERT INTO accounts (name, institution, type, currency, balance, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, institution, type_, currency, balance, notes),
    )
    db.commit()
    return cur.lastrowid


def update_account(db, account_id, name, institution, type_, currency, balance, notes):
    db.execute(
        "UPDATE accounts SET name=?, institution=?, type=?, currency=?, balance=?, notes=? "
        "WHERE id=?",
        (name, institution, type_, currency, balance, notes, account_id),
    )
    db.commit()


def delete_account(db, account_id):
    db.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    db.commit()


# --- Movimientos -------------------------------------------------------------

def list_transactions(db, account_id=None, limit=None):
    sql = (
        "SELECT t.*, a.name AS account_name, a.currency AS currency "
        "FROM transactions t JOIN accounts a ON a.id = t.account_id"
    )
    params = []
    if account_id is not None:
        sql += " WHERE t.account_id = ?"
        params.append(account_id)
    sql += " ORDER BY t.date DESC, t.id DESC"
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    return db.execute(sql, params).fetchall()


def add_transaction(db, account_id, tx_date, description, category, amount, source="manual",
                    adjust_balance=True):
    db.execute(
        "INSERT INTO transactions (account_id, date, description, category, amount, source) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (account_id, tx_date, description, category, amount, source),
    )
    if adjust_balance:
        db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, account_id))
    db.commit()


def bulk_add_transactions(db, account_id, movements, source="import", adjust_balance=True):
    total = 0.0
    for mv in movements:
        db.execute(
            "INSERT INTO transactions (account_id, date, description, category, amount, source) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (account_id, mv["date"], mv.get("description", ""), mv.get("category"), mv["amount"], source),
        )
        total += mv["amount"]
    if adjust_balance:
        db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (total, account_id))
    db.commit()
    return len(movements), total


def delete_transaction(db, tx_id):
    db.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    db.commit()


# --- Activos -----------------------------------------------------------------

def list_assets(db):
    return db.execute("SELECT * FROM assets ORDER BY name").fetchall()


def get_asset(db, asset_id):
    return db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()


def create_asset(db, name, type_, value, liability, notes):
    cur = db.execute(
        "INSERT INTO assets (name, type, value, liability, notes) VALUES (?, ?, ?, ?, ?)",
        (name, type_, value, liability, notes),
    )
    db.commit()
    return cur.lastrowid


def update_asset(db, asset_id, name, type_, value, liability, notes):
    db.execute(
        "UPDATE assets SET name=?, type=?, value=?, liability=?, notes=? WHERE id=?",
        (name, type_, value, liability, notes, asset_id),
    )
    db.commit()


def delete_asset(db, asset_id):
    db.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
    db.commit()


# --- Obligaciones / vencimientos --------------------------------------------

def list_obligations(db, order_by_due=True):
    sql = (
        "SELECT o.*, a.name AS account_name FROM obligations o "
        "LEFT JOIN accounts a ON a.id = o.account_id"
    )
    sql += " ORDER BY o.due_date" if order_by_due else " ORDER BY o.name"
    return db.execute(sql).fetchall()


def get_obligation(db, obligation_id):
    return db.execute("SELECT * FROM obligations WHERE id = ?", (obligation_id,)).fetchone()


def create_obligation(db, name, category, amount, due_date, recurrence, account_id, notes):
    cur = db.execute(
        "INSERT INTO obligations (name, category, amount, due_date, recurrence, account_id, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, category, amount, due_date, recurrence, account_id, notes),
    )
    db.commit()
    return cur.lastrowid


def update_obligation(db, obligation_id, name, category, amount, due_date, recurrence,
                      account_id, notes):
    db.execute(
        "UPDATE obligations SET name=?, category=?, amount=?, due_date=?, recurrence=?, "
        "account_id=?, notes=? WHERE id=?",
        (name, category, amount, due_date, recurrence, account_id, notes, obligation_id),
    )
    db.commit()


def delete_obligation(db, obligation_id):
    db.execute("DELETE FROM obligations WHERE id = ?", (obligation_id,))
    db.commit()


_NEXT_DELTA = {
    "mensual": lambda d: _add_months(d, 1),
    "trimestral": lambda d: _add_months(d, 3),
    "semestral": lambda d: _add_months(d, 6),
    "anual": lambda d: _add_months(d, 12),
}


def _add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    # Ajustar el día al último válido del mes destino.
    day = min(d.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


def mark_obligation_paid(db, obligation_id):
    """Marca como pagado. Si es recurrente, avanza la fecha al siguiente vencimiento."""
    obl = get_obligation(db, obligation_id)
    if obl is None:
        return
    recurrence = obl["recurrence"]
    if recurrence in _NEXT_DELTA:
        try:
            current = datetime.strptime(obl["due_date"], "%Y-%m-%d").date()
            next_due = _NEXT_DELTA[recurrence](current).strftime("%Y-%m-%d")
            db.execute("UPDATE obligations SET due_date=?, paid=0 WHERE id=?", (next_due, obligation_id))
        except ValueError:
            db.execute("UPDATE obligations SET paid=1 WHERE id=?", (obligation_id,))
    else:
        db.execute("UPDATE obligations SET paid=1 WHERE id=?", (obligation_id,))
    db.commit()


def upcoming_obligations(db, days=30):
    today = date.today()
    horizon = (today + timedelta(days=days)).strftime("%Y-%m-%d")
    return db.execute(
        "SELECT o.*, a.name AS account_name FROM obligations o "
        "LEFT JOIN accounts a ON a.id = o.account_id "
        "WHERE o.paid = 0 AND o.due_date <= ? ORDER BY o.due_date",
        (horizon,),
    ).fetchall()


# --- Resumen / patrimonio ----------------------------------------------------

def net_worth_summary(db):
    accounts_total = db.execute("SELECT COALESCE(SUM(balance), 0) AS s FROM accounts").fetchone()["s"]
    assets_value = db.execute("SELECT COALESCE(SUM(value), 0) AS s FROM assets").fetchone()["s"]
    liabilities = db.execute("SELECT COALESCE(SUM(liability), 0) AS s FROM assets").fetchone()["s"]
    return {
        "accounts_total": accounts_total,
        "assets_value": assets_value,
        "liabilities": liabilities,
        "net_worth": accounts_total + assets_value - liabilities,
    }
