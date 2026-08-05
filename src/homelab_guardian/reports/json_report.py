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