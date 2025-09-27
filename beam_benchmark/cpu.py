"""CPU benchmark routines."""
from __future__ import annotations

import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import List, Tuple

from .models import SubMetricResult
from .scoring import linear_scale


def _cpu_work(iterations: int) -> float:
    acc = 0.0
    for i in range(iterations):
        acc += math.sin(i) * math.cos(i)
    return acc


def _run_worker(duration: float, iterations: int) -> Tuple[int, float]:
    start = time.perf_counter()
    executed = 0
    while (time.perf_counter() - start) < duration:
        _cpu_work(iterations)
        executed += iterations
    elapsed = time.perf_counter() - start
    return executed, elapsed


def _single_core(duration: float) -> Tuple[float, float]:
    iterations = 100_000
    executed, elapsed = _run_worker(duration, iterations)
    ops_per_second = executed / elapsed
    return ops_per_second, elapsed


def _multi_core(duration: float, workers: int) -> Tuple[float, float]:
    iterations = 100_000
    total_executed = 0
    longest_elapsed = 0.0
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_run_worker, duration, iterations) for _ in range(workers)]
        for future in futures:
            executed, elapsed = future.result()
            total_executed += executed
            longest_elapsed = max(longest_elapsed, elapsed)
    ops_per_second = total_executed / longest_elapsed if longest_elapsed else 0.0
    return ops_per_second, longest_elapsed


def _efficiency_score(single_ops: float, multi_ops: float, workers: int) -> float:
    if not single_ops or not multi_ops or workers <= 1:
        return 0.0
    ideal = single_ops * workers
    ratio = multi_ops / ideal if ideal else 0.0
    return linear_scale(ratio, minimum=0.4, maximum=0.95)


@dataclass
class CpuBenchmark:
    single_ops: float
    multi_ops: float
    workers: int
    duration: float

    def submetrics(self) -> List[SubMetricResult]:
        single_mops = self.single_ops / 1_000_000
        multi_mops = self.multi_ops / 1_000_000

        single_score = linear_scale(single_mops, minimum=3.0, maximum=15.0)
        multi_score = linear_scale(multi_mops, minimum=10.0, maximum=120.0)
        efficiency_score = _efficiency_score(self.single_ops, self.multi_ops, self.workers)

        return [
            SubMetricResult(
                name="Rendimiento mononúcleo",
                value=round(single_mops, 2),
                unit="MOPS",
                score=single_score,
                weight=0.20,
                notes=f"Duración {self.duration:.1f}s",
            ),
            SubMetricResult(
                name="Rendimiento multinúcleo",
                value=round(multi_mops, 2),
                unit="MOPS",
                score=multi_score,
                weight=0.15,
                notes=f"{self.workers} hilos",
            ),
            SubMetricResult(
                name="Eficiencia paralela",
                value=round(self.multi_ops / self.workers / self.single_ops, 2) if self.single_ops else None,
                unit="x",
                score=efficiency_score,
                weight=0.05,
            ),
        ]


def run_cpu_benchmark(*, duration: float = 3.0, max_workers: int = 8) -> List[SubMetricResult]:
    workers = max(1, os.cpu_count() or 1)
    workers = min(workers, max_workers)
    single_ops, elapsed = _single_core(duration)
    multi_ops, _ = _multi_core(duration, workers)
    benchmark = CpuBenchmark(single_ops=single_ops, multi_ops=multi_ops, workers=workers, duration=elapsed)
    return benchmark.submetrics()
