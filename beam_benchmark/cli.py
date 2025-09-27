"""Command line interface for the Beam benchmark."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal

from .benchmark import run_benchmark
from .report import render_markdown, to_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark para hardware Beam")
    parser.add_argument("--output", "-o", type=Path, help="Ruta del informe generado")
    parser.add_argument(
        "--format",
        "-f",
        choices=("markdown", "json"),
        default="markdown",
        help="Formato del informe",
    )
    parser.add_argument("--skip-network", action="store_true", help="Omitir pruebas de red")
    parser.add_argument("--skip-gpu", action="store_true", help="Omitir detección de GPU")
    parser.add_argument(
        "--cpu-duration",
        type=float,
        default=3.0,
        help="Duración en segundos de las pruebas de CPU",
    )
    parser.add_argument(
        "--cpu-workers",
        type=int,
        default=8,
        help="Límite máximo de procesos simultáneos para la prueba de CPU",
    )
    parser.add_argument(
        "--disk-size",
        type=int,
        default=64,
        help="Tamaño del archivo temporal en MB para el benchmark de disco",
    )
    return parser.parse_args()


def build_report(output_format: Literal["markdown", "json"], **kwargs) -> str:
    result = run_benchmark(**kwargs)
    if output_format == "json":
        return to_json(result)
    return render_markdown(result)


def main() -> None:
    args = parse_args()
    report = build_report(
        args.format,
        skip_network=args.skip_network,
        skip_gpu=args.skip_gpu,
        cpu_duration=args.cpu_duration,
        cpu_max_workers=args.cpu_workers,
        disk_size_mb=args.disk_size,
    )

    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)


if __name__ == "__main__":  # pragma: no cover
    main()
