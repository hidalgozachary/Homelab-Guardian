from __future__ import annotations

import json
import subprocess
from typing import Any

from homelab_guardian.models import CollectorResult


SMARTCTL_COMMAND = "smartctl"


def run_smartctl(
    device: str,
) -> dict[str, Any]:
    """Run a read-only smartctl query and return decoded JSON."""

    command = [
        SMARTCTL_COMMAND,
        "-H",
        "-A",
        "-j",
        device,
    ]

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        return {
            "available": False,
            "payload": None,
            "error": "smartctl command is not available",
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "payload": None,
            "error": f"smartctl timed out for {device}",
        }
    except OSError as error:
        return {
            "available": False,
            "payload": None,
            "error": str(error),
        }

    stdout = completed.stdout.strip()

    if not stdout:
        error_message = (
            completed.stderr.strip()
            or f"smartctl produced no JSON for {device}"
        )

        return {
            "available": False,
            "payload": None,
            "error": error_message,
        }

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as error:
        return {
            "available": False,
            "payload": None,
            "error": f"Invalid smartctl JSON: {error}",
        }

    smartctl_data = payload.get(
        "smartctl",
        {},
    )

    exit_status = smartctl_data.get(
        "exit_status"
    )

    messages = smartctl_data.get(
        "messages",
        [],
    )

    error_messages: list[str] = []

    if isinstance(messages, list):
        for message in messages:
            if not isinstance(message, dict):
                continue

            if message.get("severity") != "error":
                continue

            text = message.get("string")

            if text:
                error_messages.append(
                    str(text)
                )

    if (
        isinstance(exit_status, int)
        and exit_status != 0
        and error_messages
    ):
        return {
            "available": False,
            "payload": payload,
            "error": "; ".join(error_messages),
        }

    return {
        "available": True,
        "payload": payload,
        "error": None,
    }


def get_ata_raw_attribute(
    payload: dict[str, Any],
    attribute_name: str,
) -> int | None:
    """Return the raw value for one ATA SMART attribute."""

    attributes = payload.get(
        "ata_smart_attributes",
        {},
    ).get(
        "table",
        [],
    )

    if not isinstance(attributes, list):
        return None

    for attribute in attributes:
        if not isinstance(attribute, dict):
            continue

        if attribute.get("name") != attribute_name:
            continue

        raw = attribute.get(
            "raw",
            {},
        )

        if not isinstance(raw, dict):
            return None

        value = raw.get(
            "value"
        )

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    return None


def normalize_smart_data(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Normalize ATA and NVMe SMART data into one schema."""

    device_data = payload.get(
        "device",
        {},
    )

    smart_status = payload.get(
        "smart_status",
        {},
    )

    temperature_data = payload.get(
        "temperature",
        {},
    )

    power_on_time = payload.get(
        "power_on_time",
        {},
    )

    protocol = device_data.get(
        "protocol"
    )

    device = device_data.get(
        "name"
    )

    passed = smart_status.get(
        "passed"
    )

    temperature_celsius = temperature_data.get(
        "current"
    )

    power_on_hours = power_on_time.get(
        "hours"
    )

    normalized = {
        "device": device,
        "protocol": protocol,
        "passed": (
            bool(passed)
            if isinstance(passed, bool)
            else None
        ),
        "status": (
            "PASSED"
            if passed is True
            else "FAILED"
            if passed is False
            else "UNKNOWN"
        ),
        "temperature_celsius": (
            int(temperature_celsius)
            if isinstance(
                temperature_celsius,
                (int, float),
            )
            else None
        ),
        "power_on_hours": (
            int(power_on_hours)
            if isinstance(
                power_on_hours,
                (int, float),
            )
            else None
        ),
        "reallocated_sectors": None,
        "pending_sectors": None,
        "uncorrectable_sectors": None,
        "crc_errors": None,
        "media_errors": None,
        "percentage_used": None,
        "critical_warning": None,
    }

    if protocol == "ATA":
        normalized[
            "reallocated_sectors"
        ] = get_ata_raw_attribute(
            payload,
            "Reallocated_Sector_Ct",
        )

        normalized[
            "pending_sectors"
        ] = get_ata_raw_attribute(
            payload,
            "Current_Pending_Sector",
        )

        normalized[
            "uncorrectable_sectors"
        ] = get_ata_raw_attribute(
            payload,
            "Offline_Uncorrectable",
        )

        normalized[
            "crc_errors"
        ] = get_ata_raw_attribute(
            payload,
            "UDMA_CRC_Error_Count",
        )

    elif protocol == "NVMe":
        nvme = payload.get(
            "nvme_smart_health_information_log",
            {},
        )

        if isinstance(nvme, dict):
            media_errors = nvme.get(
                "media_errors"
            )

            percentage_used = nvme.get(
                "percentage_used"
            )

            critical_warning = nvme.get(
                "critical_warning"
            )

            normalized[
                "media_errors"
            ] = (
                int(media_errors)
                if isinstance(
                    media_errors,
                    (int, float),
                )
                else None
            )

            normalized[
                "percentage_used"
            ] = (
                int(percentage_used)
                if isinstance(
                    percentage_used,
                    (int, float),
                )
                else None
            )

            normalized[
                "critical_warning"
            ] = (
                int(critical_warning)
                if isinstance(
                    critical_warning,
                    (int, float),
                )
                else None
            )

    return normalized


def collect_smart_for_assignments(
    assignments: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Collect SMART data for assigned storage devices."""

    results: dict[str, Any] = {}

    for name, assignment in assignments.items():
        if not assignment.get(
            "assigned"
        ):
            continue

        role = assignment.get(
            "role"
        )

        if role not in {
            "parity",
            "parity2",
            "array_disk",
            "cache",
        }:
            continue

        device_name = assignment.get(
            "device"
        )

        if not device_name:
            continue

        device_path = f"/dev/{device_name}"

        smart_result = run_smartctl(
            device_path
        )

        if not smart_result[
            "available"
        ]:
            results[name] = {
                "available": False,
                "device": device_path,
                "smart": None,
                "error": smart_result[
                    "error"
                ],
            }
            continue

        payload = smart_result.get(
            "payload"
        )

        if not isinstance(
            payload,
            dict,
        ):
            results[name] = {
                "available": False,
                "device": device_path,
                "smart": None,
                "error": (
                    "smartctl returned an invalid payload"
                ),
            }
            continue

        results[name] = {
            "available": True,
            "device": device_path,
            "smart": normalize_smart_data(
                payload
            ),
            "error": None,
        }

    return results


class SmartCollector:
    """Collect SMART health for assigned storage devices."""

    name = "smart"

    def __init__(
        self,
        assignments: dict[str, dict[str, Any]],
    ) -> None:
        self.assignments = assignments

    def collect(
        self,
    ) -> CollectorResult:
        """Return SMART information as a standardized result."""

        data = collect_smart_for_assignments(
            self.assignments
        )

        if not data:
            return CollectorResult(
                name=self.name,
                status="UNAVAILABLE",
                available=False,
                data={},
                error=None,
            )

        available_devices = [
            result
            for result in data.values()
            if (
                isinstance(result, dict)
                and result.get(
                    "available"
                )
                is True
            )
        ]

        if not available_devices:
            return CollectorResult(
                name=self.name,
                status="UNAVAILABLE",
                available=False,
                data=data,
                error=(
                    "SMART data could not be collected "
                    "from any assigned storage device"
                ),
            )

        return CollectorResult(
            name=self.name,
            status="COLLECTED",
            available=True,
            data=data,
            error=None,
        )