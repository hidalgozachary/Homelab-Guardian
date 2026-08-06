from __future__ import annotations

from pathlib import Path
from typing import Any

import psutil

from homelab_guardian.models import CollectorResult


DEFAULT_ARRAY_PATH = Path("/mnt/user")
DEFAULT_CACHE_PATH = Path("/mnt/cache")


def bytes_to_gib(value: int) -> float:
    """Convert bytes to gibibytes."""

    return round(value / (1024**3), 2)


def bytes_to_tib(value: int) -> float:
    """Convert bytes to tebibytes."""

    return round(value / (1024**4), 2)


def collect_filesystem_usage(
    path: Path,
) -> dict[str, Any]:
    """Collect capacity and utilization for one mounted path."""

    if not path.exists():
        return {
            "available": False,
            "path": str(path),
            "total_bytes": None,
            "used_bytes": None,
            "free_bytes": None,
            "percent": None,
            "total_gib": None,
            "used_gib": None,
            "free_gib": None,
            "total_tib": None,
            "used_tib": None,
            "free_tib": None,
            "error": "Path does not exist",
        }

    try:
        usage = psutil.disk_usage(str(path))
    except OSError as error:
        return {
            "available": False,
            "path": str(path),
            "total_bytes": None,
            "used_bytes": None,
            "free_bytes": None,
            "percent": None,
            "total_gib": None,
            "used_gib": None,
            "free_gib": None,
            "total_tib": None,
            "used_tib": None,
            "free_tib": None,
            "error": str(error),
        }

    return {
        "available": True,
        "path": str(path),
        "total_bytes": int(usage.total),
        "used_bytes": int(usage.used),
        "free_bytes": int(usage.free),
        "percent": round(float(usage.percent), 1),
        "total_gib": bytes_to_gib(int(usage.total)),
        "used_gib": bytes_to_gib(int(usage.used)),
        "free_gib": bytes_to_gib(int(usage.free)),
        "total_tib": bytes_to_tib(int(usage.total)),
        "used_tib": bytes_to_tib(int(usage.used)),
        "free_tib": bytes_to_tib(int(usage.free)),
        "error": None,
    }


def collect_storage_data(
    array_path: Path = DEFAULT_ARRAY_PATH,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    """Collect read-only array and cache filesystem usage."""

    array = collect_filesystem_usage(array_path)
    cache = collect_filesystem_usage(cache_path)

    return {
        "array": array,
        "cache": cache,
    }


class StorageCollector:
    """Collect array and cache capacity information."""

    name = "storage"

    def __init__(
        self,
        array_path: Path = DEFAULT_ARRAY_PATH,
        cache_path: Path = DEFAULT_CACHE_PATH,
    ) -> None:
        self.array_path = array_path
        self.cache_path = cache_path

    def collect(self) -> CollectorResult:
        """Return storage information as a standardized result."""

        data = collect_storage_data(
            array_path=self.array_path,
            cache_path=self.cache_path,
        )

        array_available = bool(
            data["array"]["available"]
        )
        cache_available = bool(
            data["cache"]["available"]
        )

        if not array_available and not cache_available:
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