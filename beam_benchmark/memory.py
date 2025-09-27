"""Memory benchmark routines."""
from __future__ import annotations

import os
import random
import time
from typing import List, Optional

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover
    psutil = None

from .models import SubMetricResult
from .scoring import linear_scale, ramp_scale


def _total_memory_gb() -> Optional[float]:
    if psutil is not None:
        return psutil.virtual_memory().total / (1024**3)
    if hasattr(os, "sysconf"):
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
        except (OSError, ValueError):
            return None
        return pages * page_size / (1024**3)
    return None


def _bandwidth_test(buffer_size: int = 64 * 1024 * 1024, passes: int = 6) -> float:
    data = bytearray(buffer_size)
    pattern = bytes([0xA5]) * 4096
    start = time.perf_counter()
    for _ in range(passes):
        view = memoryview(data)
        offset = 0
        while offset < buffer_size:
            chunk = pattern[: min(len(pattern), buffer_size - offset)]
            view[offset : offset + len(chunk)] = chunk
            offset += len(chunk)
    elapsed_write = time.perf_counter() - start

    checksum = 0
    start = time.perf_counter()
    for _ in range(passes):
        checksum += sum(data)
    elapsed_read = time.perf_counter() - start

    total_bytes = buffer_size * passes * 2
    elapsed = max(elapsed_write, 1e-9) + max(elapsed_read, 1e-9)
    throughput = total_bytes / elapsed / (1024**3)
    return throughput


def _latency_test(buffer_size: int = 16 * 1024 * 1024, samples: int = 20000) -> float:
    data = bytearray(os.urandom(buffer_size))
    indices = [random.randint(0, buffer_size - 1) for _ in range(samples)]
    start = time.perf_counter()
    total = 0
    for idx in indices:
        total += data[idx]
    elapsed = time.perf_counter() - start
    avg_ns = (elapsed / samples) * 1e9 if samples else 0.0
    return avg_ns


def run_memory_benchmark() -> List[SubMetricResult]:
    total_gb = _total_memory_gb()
    bandwidth = _bandwidth_test()
    latency_ns = _latency_test()

    capacity_score = ramp_scale(total_gb, thresholds=(8.0, 16.0, 32.0))
    bandwidth_score = linear_scale(bandwidth, minimum=5.0, maximum=35.0)
    latency_score = linear_scale(1_000.0 / latency_ns if latency_ns else None, minimum=0.2, maximum=2.0)

    return [
        SubMetricResult(
            name="Capacidad útil",
            value=round(total_gb, 2) if total_gb is not None else None,
            unit="GB",
            score=capacity_score,
            weight=0.10,
            notes="Memoria física disponible",
        ),
        SubMetricResult(
            name="Ancho de banda",
            value=round(bandwidth, 2),
            unit="GB/s",
            score=bandwidth_score,
            weight=0.07,
            notes="Prueba sintética de lectura/escritura",
        ),
        SubMetricResult(
            name="Latencia",
            value=round(latency_ns, 2),
            unit="ns",
            score=latency_score,
            weight=0.03,
            notes="Promedio de accesos aleatorios",
        ),
    ]
