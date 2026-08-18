from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def save_json_report(
    report: dict[str, Any],
    report_directory: str,
) -> Path:
    """Save a timestamped JSON health report."""

    output_directory = Path(report_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    report_path = (
        output_directory
        / f"health_report_{timestamp}.json"
    )

    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    return report_path

def find_previous_report(
    report_directory: str,
) -> Path | None:
    """Return the newest existing Guardian JSON report."""

    output_directory = Path(report_directory)

    if not output_directory.exists():
        return None

    reports = sorted(
        output_directory.glob(
            "health_report_*.json"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    return reports[0] if reports else None


def load_json_report(
    report_path: Path | None,
) -> dict[str, Any] | None:
    """Load a Guardian JSON report when available."""

    if report_path is None:
        return None

    try:
        payload = json.loads(
            report_path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return None

    if not isinstance(payload, dict):
        return None

    return payload