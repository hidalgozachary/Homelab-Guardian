from __future__ import annotations

import json
import logging
import platform
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil


CONFIG_PATH = Path("config/settings.json")
LOGGER = logging.getLogger("homelab_guardian")


def load_settings() -> dict[str, Any]:
    """Load application settings from the JSON configuration file."""

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def configure_logging(settings: dict[str, Any]) -> None:
    """Configure file and console logging."""

    log_directory = Path(settings["logging"]["directory"])
    log_directory.mkdir(parents=True, exist_ok=True)

    log_level_name = settings["logging"].get("level", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    log_file = log_directory / "guardian.log"

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def collect_system_health() -> dict[str, object]:
    """Collect basic health information from the current machine."""

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "hostname": socket.gethostname(),
        "operating_system": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "warnings": [],
        "comparison": {},
    }


def add_health_warnings(
    report: dict[str, object],
    thresholds: dict[str, float],
) -> None:
    """Add warnings when a metric exceeds its configured threshold."""

    warnings: list[str] = []

    monitored_metrics = {
        "CPU": (
            float(report["cpu_percent"]),
            float(thresholds["cpu_percent"]),
        ),
        "Memory": (
            float(report["memory_percent"]),
            float(thresholds["memory_percent"]),
        ),
        "Disk": (
            float(report["disk_percent"]),
            float(thresholds["disk_percent"]),
        ),
    }

    for name, values in monitored_metrics.items():
        current_value, warning_threshold = values

        if current_value >= warning_threshold:
            warnings.append(
                f"{name} usage is above the "
                f"{warning_threshold:.0f}% threshold: "
                f"{current_value:.1f}%"
            )

    report["warnings"] = warnings


def find_previous_report(report_directory: str) -> Path | None:
    """Return the newest existing health report, if one exists."""

    output_directory = Path(report_directory)

    if not output_directory.exists():
        return None

    report_files = sorted(
        output_directory.glob("health_report_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    return report_files[0] if report_files else None


def load_previous_report(report_path: Path | None) -> dict[str, object] | None:
    """Load the previous report from disk."""

    if report_path is None:
        return None

    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        LOGGER.warning("Unable to load previous report: %s", report_path)
        return None


def compare_with_previous(
    report: dict[str, object],
    previous_report: dict[str, object] | None,
) -> None:
    """Compare current metrics with the previous health report."""

    if previous_report is None:
        report["comparison"] = {
            "status": "No previous report available",
        }
        return

    comparison: dict[str, object] = {}

    for metric in ("cpu_percent", "memory_percent", "disk_percent"):
        current_value = float(report[metric])
        previous_value = float(previous_report.get(metric, 0.0))
        change = round(current_value - previous_value, 1)

        if change > 0:
            direction = "increased"
        elif change < 0:
            direction = "decreased"
        else:
            direction = "unchanged"

        comparison[metric] = {
            "previous": previous_value,
            "current": current_value,
            "change": change,
            "direction": direction,
        }

    report["comparison"] = comparison


def save_report(
    report: dict[str, object],
    report_directory: str,
) -> Path:
    """Save the health report as a timestamped JSON file."""

    output_directory = Path(report_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_directory / f"health_report_{timestamp}.json"

    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    return report_path


def display_comparison(report: dict[str, object]) -> None:
    """Display metric changes compared with the previous report."""

    comparison = report["comparison"]

    print("\nComparison with Previous Report")
    print("-" * 52)

    if "status" in comparison:
        print(comparison["status"])
        return

    labels = {
        "cpu_percent": "CPU",
        "memory_percent": "Memory",
        "disk_percent": "Disk",
    }

    for metric, label in labels.items():
        details = comparison[metric]
        change = float(details["change"])
        sign = "+" if change > 0 else ""

        print(
            f"{label:<10} "
            f"{float(details['previous']):>5.1f}% -> "
            f"{float(details['current']):>5.1f}% "
            f"({sign}{change:.1f}%, {details['direction']})"
        )


def display_report(
    report: dict[str, object],
    guardian_name: str,
    version: str,
) -> None:
    """Display a readable health report in the terminal."""

    print("\n" + "=" * 52)
    print(f"{guardian_name:^52}")
    print(f"{f'Version {version}':^52}")
    print("=" * 52)

    print("\nSystem Information")
    print("-" * 52)
    print(f"Hostname:          {report['hostname']}")
    print(f"Operating System:  {report['operating_system']}")
    print(f"Python Version:    {report['python_version']}")
    print(f"Report Time:       {report['timestamp']}")

    print("\nSystem Health")
    print("-" * 52)
    print(f"CPU Usage:         {float(report['cpu_percent']):.1f}%")
    print(f"Memory Usage:      {float(report['memory_percent']):.1f}%")
    print(f"Disk Usage:        {float(report['disk_percent']):.1f}%")

    display_comparison(report)

    warnings = report["warnings"]

    print("\nStatus")
    print("-" * 52)

    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}")
    else:
        print("All monitored system metrics are healthy.")

    print("=" * 52)


def main() -> int:
    """Run Homelab Guardian."""

    try:
        settings = load_settings()
        configure_logging(settings)

        LOGGER.info("Homelab Guardian started")

        report_directory = settings["reports"]["directory"]
        previous_report_path = find_previous_report(report_directory)
        previous_report = load_previous_report(previous_report_path)

        report = collect_system_health()

        add_health_warnings(
            report,
            settings["warning_thresholds"],
        )

        compare_with_previous(
            report,
            previous_report,
        )

        report_path = save_report(
            report,
            report_directory,
        )

        LOGGER.info("Health report saved to %s", report_path)

        if report["warnings"]:
            for warning in report["warnings"]:
                LOGGER.warning(warning)
        else:
            LOGGER.info("All monitored system metrics are healthy")

        display_report(
            report,
            settings["guardian_name"],
            settings["version"],
        )

        print(f"\nReport saved to: {report_path.resolve()}\n")
        return 0

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        KeyError,
        OSError,
        ValueError,
        TypeError,
    ) as error:
        LOGGER.exception("Homelab Guardian failed")
        print(f"Homelab Guardian failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())