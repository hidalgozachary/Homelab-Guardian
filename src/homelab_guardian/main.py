from __future__ import annotations

import logging

from dotenv import load_dotenv

from homelab_guardian.collectors.host import HostCollector
from homelab_guardian.collectors.network import (
    check_dns,
    check_internet,
)
from homelab_guardian.collectors.runner import run_collectors
from homelab_guardian.collectors.system import (
    collect_system_metrics,
)
from homelab_guardian.collectors.unraid import UnraidCollector
from homelab_guardian.config import load_settings
from homelab_guardian.notifications.discord import (
    send_discord_notification,
)
from homelab_guardian.reports.json_report import (
    save_json_report,
)
from homelab_guardian.reports.terminal import (
    print_terminal_report,
)
from homelab_guardian.scoring import evaluate_health


LOGGER = logging.getLogger("homelab_guardian")


def build_report(
    settings: dict[str, object],
) -> dict[str, object]:
    """Collect operational data and build the full report."""

    report = collect_system_metrics(settings)

    network_settings = settings["network"]

    report["internet"] = check_internet(
        str(network_settings["internet_url"]),
        int(network_settings["timeout_seconds"]),
    )

    report["dns"] = check_dns(
        str(network_settings["dns_hostname"])
    )

    report["collectors"] = run_collectors(
        [
            HostCollector(),
            UnraidCollector(),
        ]
    )

    report["health"] = evaluate_health(
        report,
        settings["warning_thresholds"],
    )

    return report


def main() -> int:
    """Run Homelab Guardian."""

    load_dotenv(".env")
    settings = load_settings()

    report = build_report(settings)

    report_path = save_json_report(
        report,
        str(settings["reports"]["directory"]),
    )

    print_terminal_report(
        report=report,
        guardian_name=str(settings["guardian_name"]),
        version=str(settings["version"]),
    )

    print(f"\nJSON report saved to: {report_path}")

    try:
        discord_sent = send_discord_notification(
            report=report,
            settings=settings,
        )

        if discord_sent:
            print("Discord notification sent.")

    except (ValueError, RuntimeError) as error:
        LOGGER.error(
            "Discord notification failed: %s",
            error,
        )
        print(f"Discord notification failed: {error}")

    return (
        0
        if report["health"]["status"] == "HEALTHY"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())