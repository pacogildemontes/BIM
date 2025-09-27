"""Network benchmarking routines."""
from __future__ import annotations

import json
import shutil
import subprocess
from typing import Dict, List, Optional

from .models import SubMetricResult
from .scoring import linear_scale


PING_HOST = "8.8.8.8"
PING_COUNT = 4
PING_TIMEOUT = 2


def _parse_ping(output: str) -> Optional[Dict[str, float]]:
    for line in output.splitlines():
        if "min/avg/max" in line or "min/avg/max/mdev" in line:
            stats = line.split("=")[-1].strip().split("/")
            try:
                return {
                    "min": float(stats[0]),
                    "avg": float(stats[1]),
                    "max": float(stats[2]),
                }
            except (IndexError, ValueError):
                return None
        if "round-trip" in line:
            parts = line.split("=")[-1].strip().split("/")
            try:
                return {
                    "min": float(parts[0]),
                    "avg": float(parts[1]),
                    "max": float(parts[2]),
                }
            except (IndexError, ValueError):
                return None
    return None


def _run_ping(host: str = PING_HOST) -> Optional[Dict[str, float]]:
    if shutil.which("ping") is None:
        return None
    cmd = ["ping", "-c", str(PING_COUNT), "-W", str(PING_TIMEOUT), host]
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return None
    return _parse_ping(completed.stdout)


def _run_speedtest() -> Optional[Dict[str, float]]:
    if shutil.which("speedtest"):
        cmd = ["speedtest", "--format", "json"]
    elif shutil.which("speedtest-cli"):
        cmd = ["speedtest-cli", "--json"]
    else:
        return None
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(completed.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError):
        return None

    if "download" in data and "upload" in data:
        # speedtest-cli returns bits per second
        download_mbps = data["download"] / 1_000_000
        upload_mbps = data["upload"] / 1_000_000
    elif "download" in data.get("speeds", {}):
        download_mbps = data["speeds"]["download"]
        upload_mbps = data["speeds"]["upload"]
    else:
        return None
    return {"download": download_mbps, "upload": upload_mbps}


def run_network_benchmark() -> List[SubMetricResult]:
    ping_stats = _run_ping()
    speed_stats = _run_speedtest()

    latency = ping_stats["avg"] if ping_stats else None
    download = speed_stats["download"] if speed_stats else None
    upload = speed_stats["upload"] if speed_stats else None

    latency_score = linear_scale(1000.0 / latency if latency else None, minimum=5.0, maximum=50.0)
    download_score = linear_scale(download, minimum=50.0, maximum=500.0)
    upload_score = linear_scale(upload, minimum=20.0, maximum=200.0)

    return [
        SubMetricResult(
            name="Latencia (ping)",
            value=round(latency, 2) if latency is not None else None,
            unit="ms",
            score=latency_score,
            weight=0.03,
            notes=f"Host {PING_HOST}" if ping_stats else "Ping no disponible",
        ),
        SubMetricResult(
            name="Velocidad de descarga",
            value=round(download, 2) if download is not None else None,
            unit="Mbps",
            score=download_score,
            weight=0.04,
            notes="speedtest" if speed_stats else "Sin datos",
        ),
        SubMetricResult(
            name="Velocidad de subida",
            value=round(upload, 2) if upload is not None else None,
            unit="Mbps",
            score=upload_score,
            weight=0.03,
            notes="speedtest" if speed_stats else "Sin datos",
        ),
    ]
