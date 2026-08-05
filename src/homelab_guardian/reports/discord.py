from __future__ import annotations

from typing import Any

from homelab_guardian.reports.operational import (
    build_operational_report,
)


DISCORD_COLORS = {
    "HEALTHY": 0x2ECC71,
    "WARNING": 0xF1C40F,
    "CRITICAL": 0xE74C3C,
    "UNKNOWN": 0x95A5A6,
}


def build_discord_payload(
    report: dict[str, Any],
    report_title: str,
    version: str,
) -> dict[str, object]:
    """Build a Discord webhook payload without sending it."""

    health = report.get("health", {})
    status = str(health.get("status", "UNKNOWN"))

    operational_report = build_operational_report(
        report=report,
        report_title=report_title,
        version=version,
    )

    embed_title = f"{status} - {report_title}"

    return {
        "username": "Homelab Guardian",
        "embeds": [
            {
                "title": embed_title,
                "description": operational_report,
                "color": DISCORD_COLORS.get(
                    status,
                    DISCORD_COLORS["UNKNOWN"],
                ),
                "footer": {
                    "text": (
                        f"Homelab Guardian v{version}"
                    )
                },
            }
        ],
    }