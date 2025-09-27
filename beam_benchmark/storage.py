"""Storage benchmark routines."""
from __future__ import annotations

import os
import random
import shutil
import tempfile
import time
from typing import List

from .models import SubMetricResult
from .scoring import linear_scale, ramp_scale


CHUNK_SIZE = 4 * 1024 * 1024  # 4 MiB


def _sequential_write(path: str, total_bytes: int) -> float:
    chunk = os.urandom(CHUNK_SIZE)
    written = 0
    start = time.perf_counter()
    with open(path, "wb") as f:
        while written < total_bytes:
            remaining = total_bytes - written
            f.write(chunk[: min(CHUNK_SIZE, remaining)])
            written += min(CHUNK_SIZE, remaining)
    elapsed = time.perf_counter() - start
    return total_bytes / elapsed / (1024**2)


def _sequential_read(path: str, total_bytes: int) -> float:
    read_bytes = 0
    start = time.perf_counter()
    with open(path, "rb") as f:
        while read_bytes < total_bytes:
            data = f.read(CHUNK_SIZE)
            if not data:
                break
            read_bytes += len(data)
    elapsed = time.perf_counter() - start
    return read_bytes / elapsed / (1024**2) if elapsed else 0.0


def _random_iops(path: str, iterations: int = 5000, block_size: int = 4096) -> float:
    total_ops = 0
    start = time.perf_counter()
    with open(path, "rb", buffering=0) as f:
        for _ in range(iterations):
            offset = random.randint(0, max(0, os.path.getsize(path) - block_size))
            f.seek(offset)
            f.read(block_size)
            total_ops += 1
    elapsed = time.perf_counter() - start
    return total_ops / elapsed if elapsed else 0.0


def run_storage_benchmark(*, file_size_mb: int = 64) -> List[SubMetricResult]:
    total_bytes = file_size_mb * 1024 * 1024
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    try:
        write_speed = _sequential_write(tmp_path, total_bytes)
        read_speed = _sequential_read(tmp_path, total_bytes)
        iops = _random_iops(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    usage = shutil.disk_usage(tempfile.gettempdir())
    capacity_gb = usage.total / (1024**3)
    capacity_score = ramp_scale(capacity_gb, thresholds=(256.0, 512.0, 1024.0))

    read_score = linear_scale(read_speed, minimum=50.0, maximum=3500.0)
    write_score = linear_scale(write_speed, minimum=50.0, maximum=3000.0)
    iops_score = linear_scale(iops, minimum=500.0, maximum=100_000.0)

    return [
        SubMetricResult(
            name="Capacidad total",
            value=round(capacity_gb, 2),
            unit="GB",
            score=capacity_score,
            weight=0.05,
            notes=f"Volumen en {tempfile.gettempdir()}",
        ),
        SubMetricResult(
            name="Velocidad de lectura secuencial",
            value=round(read_speed, 2),
            unit="MB/s",
            score=read_score,
            weight=0.07,
            notes=f"Archivo de {file_size_mb} MB",
        ),
        SubMetricResult(
            name="Velocidad de escritura secuencial",
            value=round(write_speed, 2),
            unit="MB/s",
            score=write_score,
            weight=0.05,
            notes=f"Archivo de {file_size_mb} MB",
        ),
        SubMetricResult(
            name="IOPS aleatorios",
            value=round(iops, 2),
            unit="operaciones/s",
            score=iops_score,
            weight=0.03,
            notes="Lecturas de 4 KiB",
        ),
    ]
