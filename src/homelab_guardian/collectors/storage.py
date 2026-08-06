from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

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


def find_mount_information(
    path: Path,
    partitions: Iterable[Any] | None = None,
) -> dict[str, str | None]:
    """Find the most specific mounted filesystem containing a path."""

    resolved_path = os.path.realpath(path)

    if partitions is None:
        try:
            partitions = psutil.disk_partitions(all=True)
        except (OSError, RuntimeError):
            partitions = []

    best_match = None
    best_mount_length = -1

    for partition in partitions:
        mountpoint = os.path.realpath(
            str(partition.mountpoint)
        )

        try:
            common_path = os.path.commonpath(
                [
                    resolved_path,
                    mountpoint,
                ]
            )
        except ValueError:
            continue

        if common_path != mountpoint:
            continue

        mount_length = len(mountpoint)

        if mount_length > best_mount_length:
            best_match = partition
            best_mount_length = mount_length

    if best_match is None:
        return {
            "device": None,
            "mountpoint": None,
            "filesystem": None,
            "mount_options": None,
        }

    return {
        "device": str(best_match.device),
        "mountpoint": str(best_match.mountpoint),
        "filesystem": str(best_match.fstype),
        "mount_options": str(best_match.opts),
    }


def unavailable_filesystem_result(
    path: Path,
    error: str,
) -> dict[str, Any]:
    """Build a consistent unavailable-filesystem result."""

    return {
        "available": False,
        "path": str(path),
        "device": None,
        "mountpoint": None,
        "filesystem": None,
        "mount_options": None,
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
        "error": error,
    }


def collect_filesystem_usage(
    path: Path,
) -> dict[str, Any]:
    """Collect capacity, utilization, and mount metadata."""

    if not path.exists():
        return unavailable_filesystem_result(
            path=path,
            error="Path does not exist",
        )

    try:
        usage = psutil.disk_usage(str(path))
    except OSError as error:
        return unavailable_filesystem_result(
            path=path,
            error=str(error),
        )

    mount_information = find_mount_information(path)

    return {
        "available": True,
        "path": str(path),
        **mount_information,
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
    """Collect read-only array and cache filesystem information."""

    array = collect_filesystem_usage(array_path)
    cache = collect_filesystem_usage(cache_path)

    return {
        "array": array,
        "cache": cache,
    }


class StorageCollector:
    """Collect array and cache filesystem information."""

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