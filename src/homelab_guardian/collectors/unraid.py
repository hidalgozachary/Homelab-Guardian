from __future__ import annotations

from pathlib import Path
from typing import Any

from homelab_guardian.models import CollectorResult


UNRAID_VERSION_PATH = Path("/etc/unraid-version")
UNRAID_VAR_PATH = Path("/var/local/emhttp/var.ini")


def detect_unraid(
    version_path: Path = UNRAID_VERSION_PATH,
) -> bool:
    """Return True when the current host appears to run Unraid."""

    return version_path.exists()


def read_key_value_file(path: Path) -> dict[str, str]:
    """Read a simple key=value configuration file."""

    values: dict[str, str] = {}

    if not path.exists():
        return values

    try:
        lines = path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()
    except OSError:
        return values

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)

        values[key.strip()] = value.strip().strip('"')

    return values


def get_unraid_version(
    version_path: Path = UNRAID_VERSION_PATH,
) -> str | None:
    """Return the installed Unraid version when available."""

    values = read_key_value_file(version_path)

    return values.get("version")


def get_unraid_variables(
    var_path: Path = UNRAID_VAR_PATH,
) -> dict[str, str]:
    """Return Unraid runtime variables from var.ini."""

    return read_key_value_file(var_path)


def get_array_state(
    var_path: Path = UNRAID_VAR_PATH,
) -> str | None:
    """Return the current Unraid array state."""

    values = get_unraid_variables(var_path)

    return values.get("mdState")


def collect_unraid_data(
    version_path: Path = UNRAID_VERSION_PATH,
    var_path: Path = UNRAID_VAR_PATH,
) -> dict[str, Any]:
    """Collect read-only Unraid-specific information."""

    is_unraid = detect_unraid(version_path)

    if not is_unraid:
        return {
            "available": False,
            "unraid_version": None,
            "array_state": None,
            "variables": {},
            "collector_status": "NOT_UNRAID",
            "error": None,
        }

    variables = get_unraid_variables(var_path)

    return {
        "available": True,
        "unraid_version": get_unraid_version(version_path),
        "array_state": variables.get("mdState"),
        "variables": variables,
        "collector_status": "COLLECTED",
        "error": None,
    }


class UnraidCollector:
    """Collect Unraid-specific operational information."""

    name = "unraid"

    def __init__(
        self,
        version_path: Path = UNRAID_VERSION_PATH,
        var_path: Path = UNRAID_VAR_PATH,
    ) -> None:
        self.version_path = version_path
        self.var_path = var_path

    def collect(self) -> CollectorResult:
        """Return Unraid information as a standardized result."""

        data = collect_unraid_data(
            version_path=self.version_path,
            var_path=self.var_path,
        )

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