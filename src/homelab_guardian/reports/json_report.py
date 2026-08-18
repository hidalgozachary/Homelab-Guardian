from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


REPORT_PATTERN = "health_report_*.json"


def save_json_report(
    report: dict[str, Any],
    report_directory: str,
) -> Path:
    """Save a timestamped JSON health report."""

    output_directory = Path(report_directory)
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    report_path = (
        output_directory
        / f"health_report_{timestamp}.json"
    )

    report_path.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    return report_path


def find_previous_report(
    report_directory: str,
) -> Path | None:
    """Return the newest existing Guardian JSON report."""

    output_directory = Path(
        report_directory
    )

    if not output_directory.exists():
        return None

    reports = sorted(
        output_directory.glob(
            REPORT_PATTERN
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    return (
        reports[0]
        if reports
        else None
    )


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

    if not isinstance(
        payload,
        dict,
    ):
        return None

    return payload


def prune_old_reports(
    report_directory: str,
    retention_days: int,
    now: datetime | None = None,
) -> list[Path]:
    """Delete Guardian reports older than the retention window."""

    if retention_days < 1:
        return []

    output_directory = Path(
        report_directory
    )

    if not output_directory.exists():
        return []

    current_time = (
        now
        if now is not None
        else datetime.now()
    )

    cutoff = (
        current_time
        - timedelta(
            days=retention_days
        )
    ).timestamp()

    deleted: list[Path] = []

    for report_path in output_directory.glob(
        REPORT_PATTERN
    ):
        try:
            modified_time = (
                report_path
                .stat()
                .st_mtime
            )
        except OSError:
            continue

        if modified_time >= cutoff:
            continue

        try:
            report_path.unlink()
        except OSError:
            continue

        deleted.append(
            report_path
        )

    return deleted