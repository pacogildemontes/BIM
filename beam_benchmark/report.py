"""Report generation helpers."""
from __future__ import annotations

import json
from typing import Iterable

from .models import BenchmarkResult, ComponentResult


def render_markdown(result: BenchmarkResult) -> str:
    lines = [
        f"# Informe Benchmark Beam",
        "",
        f"**Índice Beam:** {result.index_score:.2f} ({result.classification})",
        "",
        "## Componentes",
    ]

    for component in result.components:
        lines.extend(_render_component_markdown(component))

    if result.notes:
        lines.append("## Notas")
        for note in result.notes:
            lines.append(f"- {note}")

    lines.append("## Recomendaciones")
    if result.recommendations["impacto_inmediato"]:
        lines.append("### Impacto inmediato")
        for rec in result.recommendations["impacto_inmediato"]:
            lines.append(f"- {rec}")
    else:
        lines.append("No se identificaron mejoras rápidas.")

    if result.recommendations["plan_estrategico"]:
        lines.append("### Plan estratégico")
        for rec in result.recommendations["plan_estrategico"]:
            lines.append(f"- {rec}")
    else:
        lines.append("No se identificaron mejoras estratégicas prioritarias.")

    return "\n".join(lines)


def _render_component_markdown(component: ComponentResult) -> Iterable[str]:
    lines = [
        f"### {component.name} — puntuación {component.score:.2f}",
        "",
        "| Submétrica | Valor | Puntuación | Peso | Notas |",
        "|------------|-------|------------|------|-------|",
    ]
    for sub in component.submetrics:
        value = "-" if sub.value is None else f"{sub.value} {sub.unit or ''}".strip()
        notes = sub.notes or "-"
        lines.append(
            f"| {sub.name} | {value} | {sub.score:.2f} | {sub.weight:.2f} | {notes} |"
        )
    lines.append("")
    return lines


def to_json(result: BenchmarkResult) -> str:
    return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
