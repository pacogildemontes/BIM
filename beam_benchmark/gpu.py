"""GPU probe routines for the Beam benchmark."""
from __future__ import annotations

import shutil
import subprocess
from typing import List, Optional

from .models import SubMetricResult
from .scoring import linear_scale


_GPU_SCORE_MAP = {
    "4090": 100.0,
    "4080": 95.0,
    "4070": 85.0,
    "4060": 70.0,
    "3090": 90.0,
    "3080": 85.0,
    "3070": 75.0,
    "3060": 65.0,
    "3080 ti": 88.0,
    "a5000": 92.0,
    "a4000": 80.0,
    "quadro": 70.0,
    "rtx": 80.0,
    "gtx": 55.0,
    "rx 7900": 90.0,
    "rx 7800": 82.0,
    "rx 7700": 75.0,
    "rx 7600": 68.0,
}


def _query_nvidia_smi() -> Optional[List[dict]]:
    if shutil.which("nvidia-smi") is None:
        return None
    cmd = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,clocks.gr,clocks.sm",
        "--format=csv,noheader",
    ]
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return None
    gpus: List[dict] = []
    for line in completed.stdout.strip().splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 4:
            continue
        name, memory, graphics_clock, sm_clock = parts
        memory_value = float(memory.split()[0]) if memory else 0.0
        graphics_clock_mhz = float(graphics_clock.split()[0]) if graphics_clock else 0.0
        sm_clock_mhz = float(sm_clock.split()[0]) if sm_clock else 0.0
        gpus.append(
            {
                "name": name,
                "memory": memory_value,
                "graphics_clock": graphics_clock_mhz,
                "sm_clock": sm_clock_mhz,
            }
        )
    return gpus or None


def _fallback_gpu_info() -> Optional[List[dict]]:
    if shutil.which("lspci") is None:
        return None
    try:
        completed = subprocess.run(["lspci"], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return None
    gpus: List[dict] = []
    for line in completed.stdout.splitlines():
        if "VGA" in line or "3D controller" in line:
            gpus.append({"name": line.split(":", 1)[-1].strip(), "memory": 0.0})
    return gpus or None


def _score_from_name(name: str) -> float:
    lowered = name.lower()
    for key, score in _GPU_SCORE_MAP.items():
        if key in lowered:
            return score
    return 40.0 if name else 0.0


def run_gpu_probe() -> List[SubMetricResult]:
    gpu_data = _query_nvidia_smi()
    if gpu_data is None:
        gpu_data = _fallback_gpu_info()

    if not gpu_data:
        return [
            SubMetricResult(
                name="GPU no detectada",
                value=None,
                unit=None,
                score=0.0,
                weight=0.20,
                notes="No se pudo obtener información de GPU",
            ),
        ]

    main_gpu = gpu_data[0]
    memory_score = linear_scale(main_gpu.get("memory"), minimum=4.0, maximum=24.0)
    name_score = _score_from_name(main_gpu.get("name", ""))
    clock = main_gpu.get("graphics_clock") or main_gpu.get("sm_clock")
    clock_score = linear_scale(clock, minimum=800.0, maximum=2600.0)

    return [
        SubMetricResult(
            name="Rendimiento rasterizado (estimado)",
            value=name_score,
            unit="score",
            score=name_score,
            weight=0.12,
            notes=main_gpu.get("name"),
        ),
        SubMetricResult(
            name="Memoria de video",
            value=main_gpu.get("memory"),
            unit="GB",
            score=memory_score,
            weight=0.05,
            notes="Total detectado",
        ),
        SubMetricResult(
            name="Frecuencia GPU",
            value=clock,
            unit="MHz",
            score=clock_score,
            weight=0.03,
            notes="Máxima reportada",
        ),
    ]
