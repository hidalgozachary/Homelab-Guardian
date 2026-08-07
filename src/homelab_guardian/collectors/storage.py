from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable

import psutil

from homelab_guardian.models import CollectorResult


DEFAULT_ARRAY_PATH = Path("/mnt/user")
DEFAULT_CACHE_PATH = Path("/mnt/cache")

LSBLK_COMMAND = (
    "lsblk",
    "--json",
    "--bytes",
    "--output",
    (
        "NAME,KNAME,PATH,TYPE,SIZE,MODEL,SERIAL,"
        "FSTYPE,MOUNTPOINTS"
    ),
)


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


def normalize_mountpoints(value: object) -> list[str]:
    """Normalize lsblk mount-point data into a clean list."""

    if value is None:
        return []

    if isinstance(value, list):
        return [
            str(item)
            for item in value
            if item not in (None, "")
        ]

    text = str(value).strip()

    return [text] if text else []


def infer_device_role(
    mountpoints: list[str],
) -> str:
    """Infer a conservative device role from its mount points."""

    for mountpoint in mountpoints:
        if mountpoint == "/boot":
            return "boot"

        if mountpoint == "/mnt/cache":
            return "cache"

        if mountpoint.startswith("/mnt/disk"):
            return "array_disk"

        if mountpoint.startswith("/mnt/"):
            return "unassigned"

    return "unknown"


def parse_lsblk_device(
    raw_device: dict[str, Any],
) -> dict[str, Any]:
    """Convert one lsblk device object into the report schema."""

    mountpoints = normalize_mountpoints(
        raw_device.get("mountpoints")
    )

    size_value = raw_device.get("size")

    try:
        size_bytes = int(size_value)
    except (TypeError, ValueError):
        size_bytes = None

    return {
        "name": raw_device.get("name"),
        "kernel_name": raw_device.get("kname"),
        "path": raw_device.get("path"),
        "type": raw_device.get("type"),
        "size_bytes": size_bytes,
        "size_gib": (
            bytes_to_gib(size_bytes)
            if size_bytes is not None
            else None
        ),
        "size_tib": (
            bytes_to_tib(size_bytes)
            if size_bytes is not None
            else None
        ),
        "model": (
            str(raw_device.get("model") or "").strip()
            or None
        ),
        "serial": (
            str(raw_device.get("serial") or "").strip()
            or None
        ),
        "filesystem": raw_device.get("fstype"),
        "mountpoints": mountpoints,
        "mounted": bool(mountpoints),
        "role": infer_device_role(mountpoints),
    }


def flatten_lsblk_devices(
    raw_devices: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Flatten lsblk's nested device tree."""

    flattened: list[dict[str, Any]] = []

    def visit(device: dict[str, Any]) -> None:
        flattened.append(parse_lsblk_device(device))

        children = device.get("children", [])

        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict):
                    visit(child)

    for raw_device in raw_devices:
        if isinstance(raw_device, dict):
            visit(raw_device)

    return flattened


def collect_disk_inventory(
    command: tuple[str, ...] = LSBLK_COMMAND,
) -> dict[str, Any]:
    """Collect read-only block-device inventory using lsblk."""

    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return {
            "available": False,
            "devices": [],
            "error": "lsblk command is not available",
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "devices": [],
            "error": "lsblk command timed out",
        }
    except subprocess.CalledProcessError as error:
        message = (
            error.stderr.strip()
            if error.stderr
            else f"lsblk exited with status {error.returncode}"
        )

        return {
            "available": False,
            "devices": [],
            "error": message,
        }

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return {
            "available": False,
            "devices": [],
            "error": f"Invalid lsblk JSON: {error}",
        }

    raw_devices = payload.get("blockdevices", [])

    if not isinstance(raw_devices, list):
        return {
            "available": False,
            "devices": [],
            "error": "lsblk response did not contain a device list",
        }

    return {
        "available": True,
        "devices": flatten_lsblk_devices(raw_devices),
        "error": None,
    }


def collect_storage_data(
    array_path: Path = DEFAULT_ARRAY_PATH,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    """Collect read-only storage and device information."""

    return {
        "array": collect_filesystem_usage(array_path),
        "cache": collect_filesystem_usage(cache_path),
        "inventory": collect_disk_inventory(),
    }


class StorageCollector:
    """Collect filesystem capacity and block-device inventory."""

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
        inventory_available = bool(
            data["inventory"]["available"]
        )

        if not any(
            (
                array_available,
                cache_available,
                inventory_available,
            )
        ):
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