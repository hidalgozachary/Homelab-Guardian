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
from homelab_guardian.scoring import evaluate_health


def main() -> int:
    """Run Homelab Guardian."""

    # Load environment variables
    load_dotenv(".env")

    # Load configuration
    settings = load_settings()

    # Collect system information
    report = collect_system_metrics(settings)

    # Network checks
    network_settings = settings["network"]

    report["internet"] = check_internet(
        str(network_settings["internet_url"]),
        int(network_settings["timeout_seconds"]),
    )

    report["dns"] = check_dns(
        str(network_settings["dns_hostname"])
    )

    # Evaluate overall health
    report["health"] = evaluate_health(
        report,
        settings["warning_thresholds"],
    )

    # Temporary output while we build the reporting engine
    print(report)

    print(
        f"\nStatus: {report['health']['status']} | "
        f"Score: {report['health']['score']} / 100"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())