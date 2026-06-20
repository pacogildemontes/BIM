"""Punto de entrada WSGI para servidores de producción (gunicorn).

    gunicorn wsgi:app

La base de datos se toma de la variable de entorno FINANCE_DB (recomendado en
hosting con disco persistente) y, si se define APP_PASSWORD, la app exige login.
"""
from finanzas import create_app

app = create_app()
