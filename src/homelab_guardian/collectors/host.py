from __future__ import annotations

import os
import platform
import socket
import time
from datetime import datetime
from typing import Any

import psutil

from homelab_guardian.models import CollectorResult


def get_cpu_model() -> str:
    """Return the best available CPU model description."""

    cpu_model = platform.processor().strip()

    if cpu_model:
        return cpu_model

    cpu_info_path = "/proc/cpuinfo"

    try:
        with open(
            cpu_info_path,
            "r",
            encoding="utf-8",
            errors="replace",
        ) as cpu_info:
            for raw_line in cpu_info:
                if raw_line.lower().startswith("model name"):
                    _, value = raw_line.split(":", 1)
                    return value.strip()
    except OSError:
        pass

    machine = platform.machine().strip()

    return machine or "Unknown"


def get_cpu_temperature() -> float | None:
    """Return the first available CPU temperature in Celsius."""

    sensors_temperatures = getattr(
        psutil,
        "sensors_temperatures",
        None,
    )

    if sensors_temperatures is None:
        return None

    try:
        temperatures = sensors_temperatures(
            fahrenheit=False
        )
    except (AttributeError, OSError, RuntimeError):
        return None

    preferred_sensor_names = (
        "k10temp",
        "coretemp",
        "cpu_thermal",
    )

    for sensor_name in preferred_sensor_names:
        entries = temperatures.get(sensor_name, [])

        for entry in entries:
            if entry.current is not None:
                return round(float(entry.current), 1)

    for entries in temperatures.values():
        for entry in entries:
            if entry.current is not None:
                return round(float(entry.current), 1)

    return None


def get_load_average() -> tuple[float, float, float] | None:
    """Return one, five, and fifteen-minute load averages."""

    try:
        one, five, fifteen = os.getloadavg()
    except (AttributeError, OSError):
        return None

    return (
        round(float(one), 2),
        round(float(five), 2),
        round(float(fifteen), 2),
    )


def get_uptime_seconds() -> int:
    """Return host uptime in whole seconds."""

    return max(
        0,
        int(time.time() - psutil.boot_time()),
    )


def format_uptime(uptime_seconds: int) -> str:
    """Convert uptime seconds into a readable duration."""

    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _seconds = divmod(remainder, 60)

    parts: list[str] = []

    if days:
        parts.append(
            f"{days} day" if days == 1 else f"{days} days"
        )

    if hours:
        parts.append(
            f"{hours} hour"
            if hours == 1
            else f"{hours} hours"
        )

    if minutes or not parts:
        parts.append(
            f"{minutes} minute"
            if minutes == 1
            else f"{minutes} minutes"
        )

    return ", ".join(parts)


def collect_host_data() -> dict[str, Any]:
    """Collect read-only, platform-neutral host information."""

    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    uptime_seconds = get_uptime_seconds()
    boot_timestamp = psutil.boot_time()

    return {
        "hostname": socket.gethostname(),
        "operating_system": platform.system(),
        "platform": platform.platform(),
        "release": platform.release(),
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu": {
            "model": get_cpu_model(),
            "logical_threads": psutil.cpu_count(
                logical=True
            ),
            "physical_cores": psutil.cpu_count(
                logical=False
            ),
            "usage_percent": float(
                psutil.cpu_percent(interval=0.1)
            ),
            "temperature_celsius": get_cpu_temperature(),
        },
        "memory": {
            "total_bytes": int(memory.total),
            "available_bytes": int(memory.available),
            "used_bytes": int(memory.used),
            "percent": float(memory.percent),
        },
        "swap": {
            "total_bytes": int(swap.total),
            "used_bytes": int(swap.used),
            "free_bytes": int(swap.free),
            "percent": float(swap.percent),
        },
        "uptime_seconds": uptime_seconds,
        "uptime": format_uptime(uptime_seconds),
        "boot_time": datetime.fromtimestamp(
            boot_timestamp
        ).astimezone().isoformat(
            timespec="seconds"
        ),
        "load_average": get_load_average(),
    }


class HostCollector:
    """Collect generic host information on supported platforms."""

    name = "host"

    def collect(self) -> CollectorResult:
        """Return host information as a standardized collector result."""

        return CollectorResult(
            name=self.name,
            status="COLLECTED",
            available=True,
            data=collect_host_data(),
            error=None,
        )