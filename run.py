#!/usr/bin/env python3
"""Punto de entrada para arrancar el hub de finanzas en local.

Uso:
    python run.py
    FINANCE_DB=/ruta/mis_finanzas.db python run.py --host 0.0.0.0 --port 5000

Con --host 0.0.0.0 podrás abrirlo desde el móvil en la misma red wifi.
"""
import argparse

from finanzas import create_app


def main():
    parser = argparse.ArgumentParser(description="Hub de finanzas personales")
    parser.add_argument("--host", default="127.0.0.1",
                        help="0.0.0.0 para acceder desde otros dispositivos de la red")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
