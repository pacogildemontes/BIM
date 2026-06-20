"""Aplicación web Flask del hub de finanzas personales."""
from __future__ import annotations

import os
from datetime import date
from functools import wraps

from flask import (Flask, abort, current_app, flash, g, redirect,
                   render_template, request, session, url_for)

from . import db as db_module
from . import models
from .importer import parse_csv
from .utils import format_eur, parse_amount, parse_date

ACCOUNT_TYPES = ["banco", "tarjeta", "inversion", "efectivo"]
ASSET_TYPES = ["propiedad", "fondo", "inversion", "otro"]
PROPERTY_TYPES = ["vivienda", "local", "garaje", "terreno", "otro"]
OBLIGATION_CATEGORIES = ["seguro", "ibi", "irpf", "iva", "impuesto", "suministro",
                         "hipoteca", "comunidad", "otro"]
RECURRENCES = ["unica", "mensual", "bimestral", "trimestral", "semestral", "anual"]


def get_db():
    if "db" not in g:
        g.db = db_module.get_connection(current_app.config["DB_PATH"])
    return g.db


def create_app(db_path: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or db_module.default_db_path()
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "finanzas-local-dev")
    # Si se define APP_PASSWORD, la app exige login (necesario al desplegarla en público).
    app.config["APP_PASSWORD"] = os.environ.get("APP_PASSWORD")
    db_module.init_db(app.config["DB_PATH"])

    app.jinja_env.filters["eur"] = format_eur

    @app.teardown_appcontext
    def close_db(_exc):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    @app.before_request
    def require_login():
        if not app.config["APP_PASSWORD"]:
            return None  # sin contraseña configurada (uso local) → acceso libre
        if request.endpoint in {"login", "static"} or session.get("auth"):
            return None
        return redirect(url_for("login", next=request.path))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if not app.config["APP_PASSWORD"] or session.get("auth"):
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            if request.form.get("password") == app.config["APP_PASSWORD"]:
                session["auth"] = True
                return redirect(request.args.get("next") or url_for("dashboard"))
            flash("Contraseña incorrecta.", "error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.template_filter("dias_restantes")
    def dias_restantes(due_date):
        try:
            d = date.fromisoformat(due_date)
        except (TypeError, ValueError):
            return None
        return (d - date.today()).days

    register_routes(app)
    return app


def _amount(field, default=None):
    return parse_amount(request.form.get(field)) if request.form.get(field) else default


def register_routes(app: Flask) -> None:

    # --- Dashboard -----------------------------------------------------------
    @app.route("/")
    def dashboard():
        db = get_db()
        return render_template(
            "dashboard.html",
            summary=models.net_worth_summary(db),
            accounts=models.list_accounts(db),
            upcoming=models.upcoming_obligations(db, days=45),
            recent=models.list_transactions(db, limit=8),
            today=date.today(),
        )

    # --- Cuentas -------------------------------------------------------------
    @app.route("/cuentas")
    def accounts():
        db = get_db()
        return render_template("accounts.html", accounts=models.list_accounts(db),
                               account_types=ACCOUNT_TYPES)

    @app.route("/cuentas/nueva", methods=["POST"])
    def account_create():
        db = get_db()
        models.create_account(
            db,
            request.form["name"].strip(),
            request.form.get("institution", "").strip(),
            request.form.get("type", "banco"),
            request.form.get("currency", "EUR").strip() or "EUR",
            _amount("balance", 0) or 0,
            request.form.get("notes", "").strip(),
        )
        flash("Cuenta creada.", "success")
        return redirect(url_for("accounts"))

    @app.route("/cuentas/<int:account_id>")
    def account_detail(account_id):
        db = get_db()
        account = models.get_account(db, account_id)
        if account is None:
            abort(404)
        return render_template(
            "account_detail.html",
            account=account,
            transactions=models.list_transactions(db, account_id=account_id),
        )

    @app.route("/cuentas/<int:account_id>/editar", methods=["POST"])
    def account_update(account_id):
        db = get_db()
        models.update_account(
            db, account_id,
            request.form["name"].strip(),
            request.form.get("institution", "").strip(),
            request.form.get("type", "banco"),
            request.form.get("currency", "EUR").strip() or "EUR",
            _amount("balance", 0) or 0,
            request.form.get("notes", "").strip(),
        )
        flash("Cuenta actualizada.", "success")
        return redirect(url_for("account_detail", account_id=account_id))

    @app.route("/cuentas/<int:account_id>/borrar", methods=["POST"])
    def account_delete(account_id):
        db = get_db()
        models.delete_account(db, account_id)
        flash("Cuenta eliminada.", "success")
        return redirect(url_for("accounts"))

    # --- Movimientos ---------------------------------------------------------
    @app.route("/cuentas/<int:account_id>/movimiento", methods=["POST"])
    def transaction_create(account_id):
        db = get_db()
        amount = _amount("amount")
        tx_date = parse_date(request.form.get("date")) or date.today().isoformat()
        if amount is None:
            flash("El importe no es válido.", "error")
        else:
            models.add_transaction(
                db, account_id, tx_date,
                request.form.get("description", "").strip(),
                request.form.get("category", "").strip() or None,
                amount,
            )
            flash("Movimiento añadido.", "success")
        return redirect(url_for("account_detail", account_id=account_id))

    @app.route("/movimientos/<int:tx_id>/borrar", methods=["POST"])
    def transaction_delete(tx_id):
        db = get_db()
        models.delete_transaction(db, tx_id)
        flash("Movimiento eliminado.", "success")
        return redirect(request.referrer or url_for("dashboard"))

    # --- Importación de extractos -------------------------------------------
    @app.route("/importar", methods=["GET", "POST"])
    def import_csv():
        db = get_db()
        accounts_list = models.list_accounts(db)
        if request.method == "POST":
            account_id = request.form.get("account_id", type=int)
            file = request.files.get("file")
            if not account_id or not models.get_account(db, account_id):
                flash("Selecciona una cuenta válida.", "error")
            elif not file or not file.filename:
                flash("Selecciona un archivo CSV.", "error")
            else:
                try:
                    content = file.read().decode("utf-8-sig", errors="replace")
                    movements = parse_csv(content)
                    adjust = request.form.get("adjust_balance") == "on"
                    count, total = models.bulk_add_transactions(
                        db, account_id, movements, adjust_balance=adjust)
                    flash(f"Importados {count} movimientos (neto {format_eur(total)}).", "success")
                    return redirect(url_for("account_detail", account_id=account_id))
                except ValueError as exc:
                    flash(f"No se pudo importar: {exc}", "error")
        return render_template("import.html", accounts=accounts_list)

    # --- Activos / patrimonio ------------------------------------------------
    @app.route("/patrimonio")
    def assets():
        db = get_db()
        return render_template(
            "assets.html",
            assets=models.list_assets(db),
            asset_types=ASSET_TYPES,
            summary=models.net_worth_summary(db),
        )

    @app.route("/patrimonio/nuevo", methods=["POST"])
    def asset_create():
        db = get_db()
        models.create_asset(
            db,
            request.form["name"].strip(),
            request.form.get("type", "propiedad"),
            _amount("value", 0) or 0,
            _amount("liability", 0) or 0,
            request.form.get("notes", "").strip(),
        )
        flash("Activo añadido.", "success")
        return redirect(url_for("assets"))

    @app.route("/patrimonio/<int:asset_id>/editar", methods=["POST"])
    def asset_update(asset_id):
        db = get_db()
        models.update_asset(
            db, asset_id,
            request.form["name"].strip(),
            request.form.get("type", "propiedad"),
            _amount("value", 0) or 0,
            _amount("liability", 0) or 0,
            request.form.get("notes", "").strip(),
        )
        flash("Activo actualizado.", "success")
        return redirect(url_for("assets"))

    @app.route("/patrimonio/<int:asset_id>/borrar", methods=["POST"])
    def asset_delete(asset_id):
        db = get_db()
        models.delete_asset(db, asset_id)
        flash("Activo eliminado.", "success")
        return redirect(url_for("assets"))

    # --- Obligaciones / calendario ------------------------------------------
    @app.route("/calendario")
    def obligations():
        db = get_db()
        return render_template(
            "obligations.html",
            obligations=models.list_obligations(db),
            accounts=models.list_accounts(db),
            properties=models.list_properties(db),
            categories=OBLIGATION_CATEGORIES,
            recurrences=RECURRENCES,
            today=date.today(),
        )

    @app.route("/calendario/nueva", methods=["POST"])
    def obligation_create():
        db = get_db()
        due = parse_date(request.form.get("due_date"))
        if not due:
            flash("La fecha de vencimiento no es válida.", "error")
        else:
            models.create_obligation(
                db,
                request.form["name"].strip(),
                request.form.get("category", "otro"),
                _amount("amount"),
                due,
                request.form.get("recurrence", "unica"),
                request.form.get("account_id", type=int),
                request.form.get("notes", "").strip(),
                property_id=request.form.get("property_id", type=int),
            )
            flash("Vencimiento añadido.", "success")
        return redirect(request.form.get("redirect") or url_for("obligations"))

    @app.route("/calendario/<int:obligation_id>/editar", methods=["POST"])
    def obligation_update(obligation_id):
        db = get_db()
        due = parse_date(request.form.get("due_date"))
        if not due:
            flash("La fecha de vencimiento no es válida.", "error")
        else:
            models.update_obligation(
                db, obligation_id,
                request.form["name"].strip(),
                request.form.get("category", "otro"),
                _amount("amount"),
                due,
                request.form.get("recurrence", "unica"),
                request.form.get("account_id", type=int),
                request.form.get("notes", "").strip(),
                property_id=request.form.get("property_id", type=int),
            )
            flash("Vencimiento actualizado.", "success")
        return redirect(request.referrer or url_for("obligations"))

    @app.route("/calendario/<int:obligation_id>/pagado", methods=["POST"])
    def obligation_paid(obligation_id):
        db = get_db()
        models.mark_obligation_paid(db, obligation_id)
        flash("Marcado como pagado.", "success")
        return redirect(request.referrer or url_for("obligations"))

    @app.route("/calendario/<int:obligation_id>/borrar", methods=["POST"])
    def obligation_delete(obligation_id):
        db = get_db()
        models.delete_obligation(db, obligation_id)
        flash("Vencimiento eliminado.", "success")
        return redirect(request.referrer or url_for("obligations"))

    # --- Viviendas -----------------------------------------------------------
    @app.route("/viviendas")
    def properties():
        db = get_db()
        return render_template(
            "properties.html",
            properties=models.list_properties(db),
            property_types=PROPERTY_TYPES,
        )

    @app.route("/viviendas/nueva", methods=["POST"])
    def property_create():
        db = get_db()
        models.create_property(
            db,
            request.form["name"].strip(),
            request.form.get("address", "").strip(),
            request.form.get("type", "vivienda"),
            _amount("value", 0) or 0,
            _amount("mortgage", 0) or 0,
            _amount("purchase_price"),
            1 if request.form.get("rented") == "on" else 0,
            _amount("monthly_rent"),
            request.form.get("tenant", "").strip(),
            request.form.get("notes", "").strip(),
        )
        flash("Vivienda añadida.", "success")
        return redirect(url_for("properties"))

    @app.route("/viviendas/<int:property_id>")
    def property_detail(property_id):
        db = get_db()
        data = models.property_finances(db, property_id)
        if data is None:
            abort(404)
        return render_template(
            "property_detail.html",
            data=data,
            property=data["property"],
            accounts=models.list_accounts(db),
            categories=OBLIGATION_CATEGORIES,
            recurrences=RECURRENCES,
            property_types=PROPERTY_TYPES,
            today=date.today(),
        )

    @app.route("/viviendas/<int:property_id>/editar", methods=["POST"])
    def property_update(property_id):
        db = get_db()
        models.update_property(
            db, property_id,
            request.form["name"].strip(),
            request.form.get("address", "").strip(),
            request.form.get("type", "vivienda"),
            _amount("value", 0) or 0,
            _amount("mortgage", 0) or 0,
            _amount("purchase_price"),
            1 if request.form.get("rented") == "on" else 0,
            _amount("monthly_rent"),
            request.form.get("tenant", "").strip(),
            request.form.get("notes", "").strip(),
        )
        flash("Vivienda actualizada.", "success")
        return redirect(url_for("property_detail", property_id=property_id))

    @app.route("/viviendas/<int:property_id>/borrar", methods=["POST"])
    def property_delete(property_id):
        db = get_db()
        models.delete_property(db, property_id)
        flash("Vivienda eliminada.", "success")
        return redirect(url_for("properties"))

    # --- Inversiones (cartera ETFs/fondos) -----------------------------------
    @app.route("/inversiones")
    def investments():
        db = get_db()
        summary = models.portfolio_summary(db)
        plan = summary["plan"]
        projection = models.project_portfolio(
            summary["value"], plan["monthly_contribution"], plan["expected_return"])
        return render_template(
            "investments.html",
            summary=summary,
            plan=plan,
            projection=projection,
        )

    @app.route("/inversiones/nueva", methods=["POST"])
    def holding_create():
        db = get_db()
        models.create_holding(
            db,
            request.form.get("ticker", "").strip().upper() or None,
            request.form["name"].strip(),
            request.form.get("category", "").strip() or None,
            _amount("units", 0) or 0,
            _amount("avg_cost", 0) or 0,
            _amount("current_price"),
            _amount("target_pct"),
            request.form.get("notes", "").strip(),
        )
        flash("Posición añadida.", "success")
        return redirect(url_for("investments"))

    @app.route("/inversiones/<int:holding_id>/editar", methods=["POST"])
    def holding_update(holding_id):
        db = get_db()
        models.update_holding(
            db, holding_id,
            request.form.get("ticker", "").strip().upper() or None,
            request.form["name"].strip(),
            request.form.get("category", "").strip() or None,
            _amount("units", 0) or 0,
            _amount("avg_cost", 0) or 0,
            _amount("current_price"),
            _amount("target_pct"),
            request.form.get("notes", "").strip(),
        )
        flash("Posición actualizada.", "success")
        return redirect(url_for("investments"))

    @app.route("/inversiones/<int:holding_id>/borrar", methods=["POST"])
    def holding_delete(holding_id):
        db = get_db()
        models.delete_holding(db, holding_id)
        flash("Posición eliminada.", "success")
        return redirect(url_for("investments"))

    @app.route("/inversiones/plan", methods=["POST"])
    def plan_update():
        db = get_db()
        models.update_investment_plan(
            db,
            _amount("monthly_contribution", 0) or 0,
            _amount("expected_return", 0) or 0,
            request.form.get("notes", "").strip(),
        )
        flash("Plan de inversión actualizado.", "success")
        return redirect(url_for("investments"))
