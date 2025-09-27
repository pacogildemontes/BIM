"""Core orchestration for the Beam hardware benchmark."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from . import cpu, gpu, memory, network, storage
from .models import BenchmarkResult, ComponentResult, SubMetricResult
from .scoring import classify_index


DEFAULT_WEIGHTS = {
    "CPU": 0.40,
    "GPU": 0.20,
    "RAM": 0.15,
    "Almacenamiento": 0.15,
    "Red": 0.10,
}


def _apply_component_weight(score: float, weight: float) -> float:
    return score * weight


def _collect_recommendations(components: Iterable[ComponentResult]) -> Dict[str, List[str]]:
    focus_map = {
        "CPU": "Procesador",
        "GPU": "Tarjeta gráfica",
        "RAM": "Memoria RAM",
        "Almacenamiento": "Almacenamiento",
        "Red": "Conectividad",
    }
    quick_wins: List[str] = []
    strategic: List[str] = []

    for component in components:
        focus = focus_map.get(component.name, component.name)
        if component.score >= 75:
            continue
        if component.score < 40:
            strategic.append(
                f"{focus}: revisar actualización profunda (puntuación {component.score:.1f})."
            )
        else:
            quick_wins.append(
                f"{focus}: considerar mejoras incrementales (puntuación {component.score:.1f})."
            )

    return {
        "impacto_inmediato": quick_wins,
        "plan_estrategico": strategic,
    }


def run_benchmark(
    *,
    weights: Optional[Dict[str, float]] = None,
    skip_network: bool = False,
    skip_gpu: bool = False,
    cpu_duration: float = 3.0,
    cpu_max_workers: int = 8,
    disk_size_mb: int = 64,
) -> BenchmarkResult:
    """Execute the full benchmark pipeline."""

    weights = weights or DEFAULT_WEIGHTS

    components: List[ComponentResult] = []

    cpu_result = cpu.run_cpu_benchmark(duration=cpu_duration, max_workers=cpu_max_workers)
    components.append(ComponentResult(name="CPU", weight=weights.get("CPU", 0.0), submetrics=cpu_result))

    mem_result = memory.run_memory_benchmark()
    components.append(ComponentResult(name="RAM", weight=weights.get("RAM", 0.0), submetrics=mem_result))

    storage_result = storage.run_storage_benchmark(file_size_mb=disk_size_mb)
    components.append(
        ComponentResult(name="Almacenamiento", weight=weights.get("Almacenamiento", 0.0), submetrics=storage_result)
    )

    if skip_gpu:
        gpu_result: List[SubMetricResult] = [
            SubMetricResult(
                name="GPU no evaluada",
                value=None,
                unit=None,
                score=0.0,
                weight=1.0,
                notes="Se omitió la evaluación de GPU por configuración",
            )
        ]
    else:
        gpu_result = gpu.run_gpu_probe()
    components.append(ComponentResult(name="GPU", weight=weights.get("GPU", 0.0), submetrics=gpu_result))

    if skip_network:
        net_result: List[SubMetricResult] = [
            SubMetricResult(
                name="Red no evaluada",
                value=None,
                unit=None,
                score=0.0,
                weight=1.0,
                notes="Se omitió la evaluación de red por configuración",
            )
        ]
    else:
        net_result = network.run_network_benchmark()
    components.append(ComponentResult(name="Red", weight=weights.get("Red", 0.0), submetrics=net_result))

    weighted_scores = [_apply_component_weight(component.score, component.weight) for component in components]
    total_weight = sum(weights.get(component.name, component.weight) for component in components)
    index_score = sum(weighted_scores) / total_weight if total_weight else 0.0
    classification = classify_index(index_score)

    notes: List[str] = []
    if skip_gpu:
        notes.append("La puntuación global penaliza la ausencia de benchmark de GPU.")
    if skip_network:
        notes.append("La puntuación global no incluye mediciones de red.")

    recommendations = _collect_recommendations(components)

    return BenchmarkResult(
        components=components,
        index_score=index_score,
        classification=classification,
        notes=notes,
        recommendations=recommendations,
    )
