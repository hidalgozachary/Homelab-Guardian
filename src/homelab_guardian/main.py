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

    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())