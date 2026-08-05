from __future__ import annotations

import platform
import socket
import time
from datetime import datetime
from typing import Any

import psutil


def collect_top_processes(
    process_limit: int,
    sample_seconds: float,
) -> dict[str, list[dict[str, object]]]:
    """Collect the top processes by CPU and memory usage."""

    sampled_processes: list[psutil.Process] = []

    for process in psutil.process_iter():
        try:
            process.cpu_percent(interval=None)
            sampled_processes.append(process)
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    time.sleep(sample_seconds)

    process_results: list[dict[str, object]] = []

    for process in sampled_processes:
        try:
            memory_info = process.memory_info()

            process_results.append(
                {
                    "pid": process.pid,
                    "name": process.name() or "Unknown",
                    "username": process.username() or "Unknown",
                    "cpu_percent": round(
                        process.cpu_percent(interval=None),
                        1,
                    ),
                    "memory_mb": round(
                        memory_info.rss / (1024 * 1024),
                        1,
                    ),
                }
            )
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    return {
        "top_cpu": sorted(
            process_results,
            key=lambda item: float(item["cpu_percent"]),
            reverse=True,
        )[:process_limit],
        "top_memory": sorted(
            process_results,
            key=lambda item: float(item["memory_mb"]),
            reverse=True,
        )[:process_limit],
    }


def collect_system_metrics(
    settings: dict[str, Any],
) -> dict[str, object]:
    """Collect platform, CPU, memory, disk, and process metrics."""

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    process_settings = settings.get("process_monitoring", {})

    if process_settings.get("enabled", True):
        process_data = collect_top_processes(
            process_limit=int(
                process_settings.get("process_limit", 5)
            ),
            sample_seconds=float(
                process_settings.get("sample_seconds", 1)
            ),
        )
    else:
        process_data = {
            "top_cpu": [],
            "top_memory": [],
        }

    return {
        "timestamp": datetime.now().isoformat(
            timespec="seconds"
        ),
        "hostname": socket.gethostname(),
        "operating_system": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "processes": process_data,
    }