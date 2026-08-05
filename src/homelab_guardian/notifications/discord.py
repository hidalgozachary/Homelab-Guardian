from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from homelab_guardian.reports.discord import (
    build_discord_payload,
)


LOGGER = logging.getLogger("homelab_guardian")


def send_discord_notification(
    report: dict[str, Any],
    settings: dict[str, Any],
) -> bool:
    """Send an operational report through a Discord webhook."""

    notification_settings = settings["notifications"]

    if not notification_settings.get(
        "discord_enabled",
        False,
    ):
        LOGGER.info("Discord notifications are disabled")
        return False

    health = report.get("health", {})
    status = str(health.get("status", "UNKNOWN"))

    send_healthy_reports = bool(
        notification_settings.get(
            "send_healthy_reports",
            False,
        )
    )

    if status == "HEALTHY" and not send_healthy_reports:
        LOGGER.info("Healthy Discord report skipped")
        return False

    webhook_url = os.getenv(
        "GUARDIAN_DISCORD_WEBHOOK_URL"
    )

    if not webhook_url:
        raise ValueError(
            "GUARDIAN_DISCORD_WEBHOOK_URL is missing. "
            "Check the local .env file."
        )

    report_title = str(
        settings.get(
            "operational_report_title",
            "PandaServer Operational Report",
        )
    )

    payload = build_discord_payload(
        report=report,
        report_title=report_title,
        version=str(settings["version"]),
    )

    encoded_payload = json.dumps(payload).encode("utf-8")

    request = Request(
        webhook_url,
        data=encoded_payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Homelab-Guardian",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            status_code = int(response.status)

    except HTTPError as error:
        raise RuntimeError(
            "Discord webhook returned "
            f"HTTP {error.code}: {error.reason}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Unable to reach Discord webhook: {error.reason}"
        ) from error

    if status_code not in (200, 204):
        raise RuntimeError(
            "Discord webhook returned unexpected "
            f"HTTP status {status_code}"
        )

    LOGGER.info("Discord notification sent successfully")
    return True