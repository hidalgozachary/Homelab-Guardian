from __future__ import annotations

from dotenv import load_dotenv

from homelab_guardian.collectors.network import (
    check_dns,
    check_internet,
)
from homelab_guardian.collectors.system import (
    collect_system_metrics,
)
from homelab_guardian.config import load_settings
from homelab_guardian.reports.json_report import (
    save_json_report,
)
from homelab_guardian.reports.terminal import (
    print_terminal_report,
)
from homelab_guardian.scoring import evaluate_health


def main() -> int:
    """Run Homelab Guardian."""

    load_dotenv(".env")
    settings = load_settings()

    report = collect_system_metrics(settings)

    network_settings = settings["network"]

    report["internet"] = check_internet(
        str(network_settings["internet_url"]),
        int(network_settings["timeout_seconds"]),
    )

    report["dns"] = check_dns(
        str(network_settings["dns_hostname"])
    )

    report["health"] = evaluate_health(
        report,
        settings["warning_thresholds"],
    )

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

    return 0 if report["health"]["status"] == "HEALTHY" else 1


if __name__ == "__main__":
    raise SystemExit(main())