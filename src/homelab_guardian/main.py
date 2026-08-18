from __future__ import annotations

import logging

from dotenv import load_dotenv

from homelab_guardian.collectors.docker import (
    DockerCollector,
    add_restart_deltas,
)
from homelab_guardian.collectors.host import HostCollector
from homelab_guardian.collectors.kernel import KernelHealthCollector
from homelab_guardian.collectors.network import (
    check_dns,
    check_internet,
)
from homelab_guardian.collectors.runner import run_collectors
from homelab_guardian.collectors.smart import SmartCollector
from homelab_guardian.collectors.storage import StorageCollector
from homelab_guardian.collectors.system import (
    collect_system_metrics,
)
from homelab_guardian.collectors.unraid import UnraidCollector
from homelab_guardian.config import load_settings
from homelab_guardian.notifications.discord import (
    send_discord_notification,
)
from homelab_guardian.reports.json_report import (
    find_previous_report,
    load_json_report,
    prune_old_reports,
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

    base_collectors = run_collectors(
        [
            HostCollector(),
            KernelHealthCollector(),
            UnraidCollector(),
            StorageCollector(),
            DockerCollector(),
        ]
    )

    unraid_data = (
        base_collectors
        .get("unraid", {})
        .get("data", {})
    )

    disk_assignments = unraid_data.get(
        "disk_assignments",
        {}
    )

    smart_collectors = run_collectors(
        [
            SmartCollector(
                assignments=disk_assignments
            ),
        ]
    )

    report["collectors"] = {
        **base_collectors,
        **smart_collectors,
    }

    previous_report = None

    reports_settings = settings.get(
        "reports",
        {},
    )

    if isinstance(reports_settings, dict):
        report_directory = reports_settings.get(
            "directory"
        )

        if report_directory:
            previous_report = load_json_report(
                find_previous_report(
                    str(report_directory)
                )
            )

    docker_collector = report["collectors"].get(
        "docker",
        {},
    )

    if isinstance(docker_collector, dict):
        docker_data = docker_collector.get(
            "data",
            {},
        )

        if isinstance(docker_data, dict):
            containers = docker_data.get(
                "containers",
                [],
            )

            if isinstance(containers, list):
                add_restart_deltas(
                    containers,
                    previous_report,
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

    reports_settings = settings[
        "reports"
    ]

    report_directory = str(
        reports_settings["directory"]
    )

    report_path = save_json_report(
        report,
        report_directory,
    )

    retention_days = int(
        reports_settings.get(
            "retention_days",
            30,
        )
    )

    prune_old_reports(
        report_directory,
        retention_days,
    )

    print_terminal_report(
        report=report,
        guardian_name=str(
            settings["guardian_name"]
        ),
        version=str(
            settings["version"]
        ),
    )

    print(
        f"\nJSON report saved to: {report_path}"
    )

    try:
        discord_sent = send_discord_notification(
            report=report,
            settings=settings,
        )

        if discord_sent:
            print(
                "Discord notification sent."
            )

    except (
        ValueError,
        RuntimeError,
    ) as error:
        LOGGER.error(
            "Discord notification failed: %s",
            error,
        )

        print(
            f"Discord notification failed: {error}"
        )

    return (
        0
        if report["health"]["status"]
        == "HEALTHY"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )