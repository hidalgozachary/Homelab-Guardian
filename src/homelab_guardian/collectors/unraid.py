from __future__ import annotations

from pathlib import Path
from typing import Any

from homelab_guardian.models import CollectorResult


UNRAID_VERSION_PATH = Path("/etc/unraid-version")
UNRAID_VAR_PATH = Path("/var/local/emhttp/var.ini")
UNRAID_DISKS_PATH = Path("/var/local/emhttp/disks.ini")


def detect_unraid(
    version_path: Path = UNRAID_VERSION_PATH,
) -> bool:
    """Return True when the current host appears to run Unraid."""

    return version_path.exists()


def read_key_value_file(
    path: Path,
) -> dict[str, str]:
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

        key, value = line.split(
            "=",
            1,
        )

        values[
            key.strip()
        ] = value.strip().strip('"')

    return values


def read_sectioned_key_value_file(
    path: Path,
) -> dict[str, dict[str, str]]:
    """Read an Unraid sectioned key=value runtime file."""

    sections: dict[str, dict[str, str]] = {}

    if not path.exists():
        return sections

    try:
        lines = path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()
    except OSError:
        return sections

    current_section: str | None = None

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            continue

        if (
            line.startswith("[")
            and line.endswith("]")
        ):
            section_name = (
                line[1:-1]
                .strip()
                .strip('"')
            )

            if section_name:
                current_section = (
                    section_name
                )

                sections[
                    current_section
                ] = {}

            continue

        if current_section is None:
            continue

        if "=" not in line:
            continue

        key, value = line.split(
            "=",
            1,
        )

        sections[current_section][
            key.strip()
        ] = value.strip().strip('"')

    return sections


def get_unraid_version(
    version_path: Path = UNRAID_VERSION_PATH,
) -> str | None:
    """Return the installed Unraid version when available."""

    values = read_key_value_file(
        version_path
    )

    return values.get(
        "version"
    )


def get_unraid_variables(
    var_path: Path = UNRAID_VAR_PATH,
) -> dict[str, str]:
    """Return Unraid runtime variables from var.ini."""

    return read_key_value_file(
        var_path
    )


def get_array_state(
    var_path: Path = UNRAID_VAR_PATH,
) -> str | None:
    """Return the current Unraid array state."""

    values = get_unraid_variables(
        var_path
    )

    return values.get(
        "mdState"
    )


def normalize_disk_role(
    name: str,
    disk_type: str | None = None,
) -> str:
    """Convert Unraid disk names into stable Guardian roles."""

    normalized_name = name.lower()

    if normalized_name == "parity":
        return "parity"

    if normalized_name.startswith(
        "parity"
    ):
        return normalized_name

    if normalized_name.startswith(
        "disk"
    ):
        return "array_disk"

    if normalized_name == "cache":
        return "cache"

    if normalized_name == "flash":
        return "flash"

    normalized_type = (
        disk_type
        or ""
    ).lower()

    if normalized_type == "parity":
        return "parity"

    if normalized_type == "data":
        return "array_disk"

    if normalized_type == "cache":
        return "cache"

    if normalized_type == "flash":
        return "flash"

    return "unknown"


def get_disk_assignments(
    disks_path: Path = UNRAID_DISKS_PATH,
) -> dict[str, dict[str, Any]]:
    """Return normalized Unraid disk assignments."""

    raw_sections = (
        read_sectioned_key_value_file(
            disks_path
        )
    )

    assignments: dict[
        str,
        dict[str, Any],
    ] = {}

    for (
        section_name,
        values,
    ) in raw_sections.items():
        device = (
            values.get("device")
            or None
        )

        disk_id = (
            values.get("id")
            or None
        )

        try:
            size = int(
                values.get(
                    "size",
                    "0",
                )
            )
        except ValueError:
            size = 0

        assigned = bool(
            device
            and disk_id
            and size > 0
        )

        temperature_raw = (
            values.get("temp")
        )

        temperature: int | None

        try:
            temperature = (
                int(
                    temperature_raw
                )
                if temperature_raw
                not in (
                    None,
                    "",
                    "*",
                )
                else None
            )
        except ValueError:
            temperature = None

        errors_raw = (
            values.get(
                "numErrors"
            )
        )

        try:
            errors = (
                int(errors_raw)
                if errors_raw
                not in (
                    None,
                    "",
                )
                else None
            )
        except ValueError:
            errors = None

        assignments[
            section_name
        ] = {
            "name": section_name,
            "role": normalize_disk_role(
                section_name,
                values.get("type"),
            ),
            "assigned": assigned,
            "device": device,
            "id": disk_id,
            "type": (
                values.get("type")
                or None
            ),
            "status": (
                values.get("status")
                or None
            ),
            "filesystem": (
                values.get("fsType")
                or None
            ),
            "filesystem_status": (
                values.get("fsStatus")
                or None
            ),
            "mountpoint": (
                values.get(
                    "fsMountpoint"
                )
                or None
            ),
            "temperature_celsius": (
                temperature
            ),
            "errors": errors,
            "color": (
                values.get("color")
                or None
            ),
            "size": size,
        }

    return assignments


def collect_unraid_data(
    version_path: Path = UNRAID_VERSION_PATH,
    var_path: Path = UNRAID_VAR_PATH,
    disks_path: Path = UNRAID_DISKS_PATH,
) -> dict[str, Any]:
    """Collect sanitized read-only Unraid information."""

    is_unraid = detect_unraid(
        version_path
    )

    if not is_unraid:
        return {
            "available": False,
            "unraid_version": None,
            "array_state": None,
            "disk_assignments": {},
            "collector_status": (
                "NOT_UNRAID"
            ),
            "error": None,
        }

    variables = get_unraid_variables(
        var_path
    )

    return {
        "available": True,
        "unraid_version": (
            get_unraid_version(
                version_path
            )
        ),
        "array_state": (
            variables.get(
                "mdState"
            )
        ),
        "disk_assignments": (
            get_disk_assignments(
                disks_path
            )
        ),
        "collector_status": (
            "COLLECTED"
        ),
        "error": None,
    }


class UnraidCollector:
    """Collect Unraid-specific operational information."""

    name = "unraid"

    def __init__(
        self,
        version_path: Path = UNRAID_VERSION_PATH,
        var_path: Path = UNRAID_VAR_PATH,
        disks_path: Path = UNRAID_DISKS_PATH,
    ) -> None:
        self.version_path = (
            version_path
        )
        self.var_path = (
            var_path
        )
        self.disks_path = (
            disks_path
        )

    def collect(
        self,
    ) -> CollectorResult:
        """Return Unraid information as a standardized result."""

        data = collect_unraid_data(
            version_path=(
                self.version_path
            ),
            var_path=(
                self.var_path
            ),
            disks_path=(
                self.disks_path
            ),
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