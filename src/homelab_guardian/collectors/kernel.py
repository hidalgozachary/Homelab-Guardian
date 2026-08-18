from __future__ import annotations

import re
import subprocess
from typing import Any

from homelab_guardian.models import CollectorResult


DMESG_COMMAND = (
    "dmesg",
    "--color=never",
)


EVENT_PATTERNS: dict[str, tuple[str, ...]] = {
    "kernel_fault": (
        r"\bBUG:",
        r"\bOops:",
        r"\bkernel panic\b",
        r"\bpage fault\b",
    ),
    "rcu_stall": (
        r"\brcu.*stall\b",
    ),
    "hardware_error": (
        r"\bMachine Check Exception\b",
        r"\bMachine Check Event\b",
        r"\bMCE:.*\berror\b",
        r"\bHardware Error\b",
        r"\bEDAC\b.*\berror\b",
        r"\bEDAC\b.*\buncorrected\b",
        r"\bEDAC\b.*\bcorrected error\b",
    ),
    "oom": (
        r"\bOut of memory\b",
        r"\bKilled process\b",
        r"\boom-kill\b",
    ),
    "btrfs_error": (
        r"\bBTRFS\b.*\berror\b",
        r"\bBTRFS\b.*\bcorrupt",
    ),
    "xfs_error": (
        r"\bXFS\b.*\berror\b",
        r"\bXFS\b.*\bcorrupt",
    ),
    "io_error": (
        r"\bI/O error\b",
        r"\bBuffer I/O error\b",
    ),
    "nvme_error": (
        r"\bnvme\b.*\btimeout\b",
        r"\bnvme\b.*\breset\b",
        r"\bnvme\b.*\berror\b",
    ),
    "disk_reset": (
        r"\bhard resetting link\b",
        r"\bresetting link\b",
        r"\bdevice reset\b",
    ),
}


def run_dmesg() -> dict[str, Any]:
    """Read the current kernel log using dmesg."""

    try:
        completed = subprocess.run(
            DMESG_COMMAND,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return {
            "available": False,
            "output": "",
            "error": "dmesg command is not available",
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "output": "",
            "error": "dmesg command timed out",
        }
    except OSError as error:
        return {
            "available": False,
            "output": "",
            "error": str(error),
        }

    output = completed.stdout.strip()

    if completed.returncode != 0:
        error_message = completed.stderr.strip()

        if not error_message:
            error_message = (
                "dmesg returned a non-zero exit status"
            )

        return {
            "available": False,
            "output": output,
            "error": error_message,
        }

    return {
        "available": True,
        "output": output,
        "error": None,
    }


def classify_kernel_events(
    output: str,
) -> dict[str, Any]:
    """Classify high-signal events from kernel-log output."""

    events: dict[str, list[str]] = {
        category: []
        for category in EVENT_PATTERNS
    }

    for raw_line in output.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        for category, patterns in EVENT_PATTERNS.items():
            matched = any(
                re.search(
                    pattern,
                    line,
                    flags=re.IGNORECASE,
                )
                is not None
                for pattern in patterns
            )

            if matched:
                events[category].append(line)

    counts: dict[str, int] = {
        category: len(category_events)
        for category, category_events in events.items()
    }

    total_events = sum(counts.values())

    return {
        "total_events": total_events,
        "counts": counts,
        "events": events,
    }


def collect_kernel_health() -> dict[str, Any]:
    """Collect and normalize kernel-health information."""

    dmesg_result = run_dmesg()

    if not dmesg_result["available"]:
        return {
            "available": False,
            "total_events": 0,
            "counts": {},
            "events": {},
            "error": dmesg_result["error"],
        }

    output = dmesg_result.get(
        "output",
        "",
    )

    if not isinstance(output, str):
        return {
            "available": False,
            "total_events": 0,
            "counts": {},
            "events": {},
            "error": "dmesg returned invalid output",
        }

    classified = classify_kernel_events(
        output
    )

    return {
        "available": True,
        **classified,
        "error": None,
    }


class KernelHealthCollector:
    """Collect high-signal kernel and hardware health events."""

    name = "kernel_health"

    def collect(self) -> CollectorResult:
        """Return standardized kernel-health information."""

        data = collect_kernel_health()

        if not data["available"]:
            return CollectorResult(
                name=self.name,
                status="UNAVAILABLE",
                available=False,
                data=data,
                error=str(
                    data.get("error")
                    or "Kernel health unavailable"
                ),
            )

        return CollectorResult(
            name=self.name,
            status="COLLECTED",
            available=True,
            data=data,
            error=None,
        )