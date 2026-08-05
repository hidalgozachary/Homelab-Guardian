from __future__ import annotations

import os
import platform
import socket
from pathlib import Path
from typing import Any

import psutil
from homelab_guardian.models import CollectorResult


UNRAID_VERSION_PATH = Path("/etc/unraid-version")
UNRAID_VAR_PATH = Path("/var/local/emhttp/var.ini")


def detect_unraid() -> bool:
    """Return True when the current host appears to be running Unraid."""

    return UNRAID_VERSION_PATH.exists()


def read_key_value_file(path: Path) -> dict[str, str]:
    """Read a simple key=value file into a dictionary."""

    values: dict[str, str] = {}

    if not path.exists():
        return values

    try:
        for raw_line in path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)

            values[key.strip()] = value.strip().strip('"')

    except OSError:
        return {}

    return values


def get_unraid_version() -> str | None:
    """Return the installed Unraid version when available."""

    version_data = read_key_value_file(
        UNRAID_VERSION_PATH
    )

    return version_data.get("version")


def get_array_state() -> str | None:
    """Return the current Unraid array state when available."""

    unraid_values = read_key_value_file(
        UNRAID_VAR_PATH
    )

    return unraid_values.get("mdState")


def get_cpu_temperature() -> float | None:
    """Return the first available CPU temperature in Celsius.

    Some platforms, including macOS, do not expose
    psutil.sensors_temperatures().
    """

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
    """Return the one, five, and fifteen-minute load averages."""

    try:
        load_one, load_five, load_fifteen = os.getloadavg()
    except (AttributeError, OSError):
        return None

    return (
        round(load_one, 2),
        round(load_five, 2),
        round(load_fifteen, 2),
    )


def get_uptime_seconds() -> int:
    """Return host uptime in whole seconds."""

    return max(
        0,
        int(psutil.time.time() - psutil.boot_time()),
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
            f"{hours} hour" if hours == 1 else f"{hours} hours"
        )

    if minutes or not parts:
        parts.append(
            f"{minutes} minute"
            if minutes == 1
            else f"{minutes} minutes"
        )

    return ", ".join(parts)


def collect_unraid_host() -> dict[str, Any]:
    """Collect read-only Unraid and host-level information."""

    is_unraid = detect_unraid()
    memory = psutil.virtual_memory()
    uptime_seconds = get_uptime_seconds()

    return {
        "available": is_unraid,
        "platform": (
            "Unraid"
            if is_unraid
            else platform.system()
        ),
        "hostname": socket.gethostname(),
        "unraid_version": (
            get_unraid_version()
            if is_unraid
            else None
        ),
        "array_state": (
            get_array_state()
            if is_unraid
            else None
        ),
        "uptime_seconds": uptime_seconds,
        "uptime": format_uptime(uptime_seconds),
        "load_average": get_load_average(),
        "cpu_temperature": get_cpu_temperature(),
        "memory": {
            "total_bytes": int(memory.total),
            "available_bytes": int(memory.available),
            "used_bytes": int(memory.used),
            "percent": float(memory.percent),
        },
        "collector_status": (
            "COLLECTED"
            if is_unraid
            else "NOT_UNRAID"
        ),
        "error": None,
    }
class UnraidCollector:
    """Collect Unraid host information through the collector framework."""

    name = "unraid"

    def collect(self) -> CollectorResult:
        """Collect Unraid data and return a standardized result."""

        data = collect_unraid_host()

        if not data["available"]:
            return CollectorResult(
                name=self.name,
                status="UNAVAILABLE",
                available=False,
                data=data,
                error=None,
            )

        return CollectorResult(
            name=self.name,
            status="COLLECTED",
            available=True,
            data=data,
            error=None,
        )