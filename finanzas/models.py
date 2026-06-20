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

def list_obligations(db, order_by_due=True, property_id=None):
    sql = (
        "SELECT o.*, a.name AS account_name, p.name AS property_name FROM obligations o "
        "LEFT JOIN accounts a ON a.id = o.account_id "
        "LEFT JOIN properties p ON p.id = o.property_id"
    )
    params = []
    if property_id is not None:
        sql += " WHERE o.property_id = ?"
        params.append(property_id)
    sql += " ORDER BY o.due_date" if order_by_due else " ORDER BY o.name"
    return db.execute(sql, params).fetchall()


def get_obligation(db, obligation_id):
    return db.execute("SELECT * FROM obligations WHERE id = ?", (obligation_id,)).fetchone()


def create_obligation(db, name, category, amount, due_date, recurrence, account_id, notes,
                      property_id=None):
    cur = db.execute(
        "INSERT INTO obligations (name, category, amount, due_date, recurrence, account_id, "
        "property_id, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (name, category, amount, due_date, recurrence, account_id, property_id, notes),
    )
    db.commit()
    return cur.lastrowid


def update_obligation(db, obligation_id, name, category, amount, due_date, recurrence,
                      account_id, notes, property_id=None):
    db.execute(
        "UPDATE obligations SET name=?, category=?, amount=?, due_date=?, recurrence=?, "
        "account_id=?, property_id=?, notes=? WHERE id=?",
        (name, category, amount, due_date, recurrence, account_id, property_id, notes, obligation_id),
    )
    db.commit()


def delete_obligation(db, obligation_id):
    db.execute("DELETE FROM obligations WHERE id = ?", (obligation_id,))
    db.commit()


_NEXT_DELTA = {
    "mensual": lambda d: _add_months(d, 1),
    "bimestral": lambda d: _add_months(d, 2),
    "trimestral": lambda d: _add_months(d, 3),
    "semestral": lambda d: _add_months(d, 6),
    "anual": lambda d: _add_months(d, 12),
}

# Cuántas veces al año se paga cada recurrencia (para anualizar gastos).
PER_YEAR = {"mensual": 12, "bimestral": 6, "trimestral": 4, "semestral": 2, "anual": 1, "unica": 0}


def annualize(amount, recurrence):
    return (amount or 0) * PER_YEAR.get(recurrence, 0)


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


# --- Viviendas / inmuebles ---------------------------------------------------

def list_properties(db):
    return db.execute("SELECT * FROM properties ORDER BY name").fetchall()


def get_property(db, property_id):
    return db.execute("SELECT * FROM properties WHERE id = ?", (property_id,)).fetchone()


def create_property(db, name, address, type_, value, mortgage, purchase_price,
                    rented, monthly_rent, tenant, notes):
    cur = db.execute(
        "INSERT INTO properties (name, address, type, value, mortgage, purchase_price, "
        "rented, monthly_rent, tenant, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, address, type_, value, mortgage, purchase_price, rented, monthly_rent, tenant, notes),
    )
    db.commit()
    return cur.lastrowid


def update_property(db, property_id, name, address, type_, value, mortgage, purchase_price,
                    rented, monthly_rent, tenant, notes):
    db.execute(
        "UPDATE properties SET name=?, address=?, type=?, value=?, mortgage=?, purchase_price=?, "
        "rented=?, monthly_rent=?, tenant=?, notes=? WHERE id=?",
        (name, address, type_, value, mortgage, purchase_price, rented, monthly_rent, tenant,
         notes, property_id),
    )
    db.commit()


def delete_property(db, property_id):
    db.execute("DELETE FROM properties WHERE id = ?", (property_id,))
    db.commit()


def property_finances(db, property_id):
    """Resumen económico de una vivienda: gastos anuales y rentabilidad neta."""
    prop = get_property(db, property_id)
    if prop is None:
        return None
    obligations = list_obligations(db, property_id=property_id)
    annual_expenses = sum(annualize(o["amount"], o["recurrence"]) for o in obligations)
    # Gastos de pago único: se cuentan tal cual en el total anual aproximado.
    annual_expenses += sum((o["amount"] or 0) for o in obligations if o["recurrence"] == "unica")
    annual_rent = (prop["monthly_rent"] or 0) * 12 if prop["rented"] else 0
    net_annual = annual_rent - annual_expenses
    net_equity = (prop["value"] or 0) - (prop["mortgage"] or 0)
    gross_yield = (annual_rent / prop["value"] * 100) if prop["value"] else None
    net_yield = (net_annual / prop["value"] * 100) if prop["value"] else None
    return {
        "property": prop,
        "obligations": obligations,
        "annual_expenses": annual_expenses,
        "annual_rent": annual_rent,
        "net_annual": net_annual,
        "net_equity": net_equity,
        "gross_yield": gross_yield,
        "net_yield": net_yield,
    }


# --- Cartera de inversión (ETFs/fondos) -------------------------------------

def list_holdings(db):
    return db.execute("SELECT * FROM holdings ORDER BY name").fetchall()


def get_holding(db, holding_id):
    return db.execute("SELECT * FROM holdings WHERE id = ?", (holding_id,)).fetchone()


def create_holding(db, ticker, name, category, units, avg_cost, current_price, target_pct, notes):
    cur = db.execute(
        "INSERT INTO holdings (ticker, name, category, units, avg_cost, current_price, "
        "target_pct, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (ticker, name, category, units, avg_cost, current_price, target_pct, notes),
    )
    db.commit()
    return cur.lastrowid


def update_holding(db, holding_id, ticker, name, category, units, avg_cost, current_price,
                   target_pct, notes):
    db.execute(
        "UPDATE holdings SET ticker=?, name=?, category=?, units=?, avg_cost=?, current_price=?, "
        "target_pct=?, notes=? WHERE id=?",
        (ticker, name, category, units, avg_cost, current_price, target_pct, notes, holding_id),
    )
    db.commit()


def delete_holding(db, holding_id):
    db.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
    db.commit()


def get_investment_plan(db):
    return db.execute("SELECT * FROM investment_plan WHERE id = 1").fetchone()


def update_investment_plan(db, monthly_contribution, expected_return, notes):
    db.execute(
        "UPDATE investment_plan SET monthly_contribution=?, expected_return=?, notes=? WHERE id=1",
        (monthly_contribution, expected_return, notes),
    )
    db.commit()


def _holding_value(h):
    price = h["current_price"] if h["current_price"] is not None else h["avg_cost"]
    return (h["units"] or 0) * (price or 0)


def portfolio_summary(db):
    holdings = list_holdings(db)
    invested = sum((h["units"] or 0) * (h["avg_cost"] or 0) for h in holdings)
    value = sum(_holding_value(h) for h in holdings)
    rows = []
    for h in holdings:
        v = _holding_value(h)
        cost = (h["units"] or 0) * (h["avg_cost"] or 0)
        rows.append({
            "h": h,
            "value": v,
            "cost": cost,
            "pl": v - cost,
            "pl_pct": ((v - cost) / cost * 100) if cost else None,
            "weight": (v / value * 100) if value else None,
            "drift": ((v / value * 100) - h["target_pct"]) if (value and h["target_pct"] is not None) else None,
        })
    return {
        "rows": rows,
        "invested": invested,
        "value": value,
        "pl": value - invested,
        "pl_pct": ((value - invested) / invested * 100) if invested else None,
        "plan": get_investment_plan(db),
    }


def project_portfolio(value, monthly_contribution, annual_return_pct, years=20):
    """Proyección simple con interés compuesto mensual y aportación periódica."""
    r = (annual_return_pct or 0) / 100 / 12
    horizons = [1, 3, 5, 10, 15, 20]
    horizons = [y for y in horizons if y <= years]
    projection = []
    for y in horizons:
        months = y * 12
        fv = value * ((1 + r) ** months)
        if r:
            fv += monthly_contribution * (((1 + r) ** months - 1) / r)
        else:
            fv += monthly_contribution * months
        contributed = value + monthly_contribution * months
        projection.append({
            "years": y,
            "value": fv,
            "contributed": contributed,
            "gains": fv - contributed,
        })
    return projection


# --- Resumen / patrimonio ----------------------------------------------------

def net_worth_summary(db):
    accounts_total = db.execute("SELECT COALESCE(SUM(balance), 0) AS s FROM accounts").fetchone()["s"]
    other_assets = db.execute("SELECT COALESCE(SUM(value - liability), 0) AS s FROM assets").fetchone()["s"]
    prop = db.execute(
        "SELECT COALESCE(SUM(value), 0) AS v, COALESCE(SUM(mortgage), 0) AS m FROM properties"
    ).fetchone()
    properties_value = prop["v"]
    mortgages = prop["m"]
    investments_value = portfolio_summary(db)["value"]
    net_worth = accounts_total + other_assets + investments_value + properties_value - mortgages
    return {
        "accounts_total": accounts_total,
        "properties_value": properties_value,
        "mortgages": mortgages,
        "investments_value": investments_value,
        "other_assets": other_assets,
        "liabilities": mortgages,
        "net_worth": net_worth,
    }
