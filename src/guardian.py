from __future__ import annotations

import json
import logging
import os
import platform
import smtplib
import socket
import sys
import time
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import psutil
from dotenv import load_dotenv


CONFIG_PATH = Path("config/settings.json")
ENV_PATH = Path(".env")
LOGGER = logging.getLogger("homelab_guardian")


def load_settings() -> dict[str, Any]:
    """Load Homelab Guardian settings from JSON."""

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_PATH}"
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def configure_logging(settings: dict[str, Any]) -> None:
    """Configure console and file logging."""

    log_directory = Path(settings["logging"]["directory"])
    log_directory.mkdir(parents=True, exist_ok=True)

    requested_level = str(
        settings["logging"].get("level", "INFO")
    ).upper()

    log_level = getattr(
        logging,
        requested_level,
        logging.INFO,
    )

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(
                log_directory / "guardian.log",
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
        force=True,
    )


def check_internet(
    url: str,
    timeout_seconds: int,
) -> dict[str, object]:
    """Check internet reachability and response time."""

    started = time.perf_counter()

    try:
        with urlopen(url, timeout=timeout_seconds) as response:
            response_time_ms = round(
                (time.perf_counter() - started) * 1000,
                1,
            )

            return {
                "reachable": True,
                "status_code": response.status,
                "response_time_ms": response_time_ms,
                "error": None,
            }

    except (URLError, TimeoutError, OSError) as error:
        response_time_ms = round(
            (time.perf_counter() - started) * 1000,
            1,
        )

        return {
            "reachable": False,
            "status_code": None,
            "response_time_ms": response_time_ms,
            "error": str(error),
        }


def check_dns(hostname: str) -> dict[str, object]:
    """Resolve a hostname to verify DNS functionality."""

    try:
        return {
            "resolved": True,
            "hostname": hostname,
            "ip_address": socket.gethostbyname(hostname),
            "error": None,
        }

    except socket.gaierror as error:
        return {
            "resolved": False,
            "hostname": hostname,
            "ip_address": None,
            "error": str(error),
        }


def collect_top_processes(
    process_limit: int,
    sample_seconds: float,
) -> dict[str, list[dict[str, object]]]:
    """Collect the top processes by CPU and memory usage."""

    sampled_processes: list[psutil.Process] = []

    for process in psutil.process_iter():
        try:
            process.cpu_percent(interval=None)
            sampled_processes.append(process)

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    time.sleep(sample_seconds)

    process_results: list[dict[str, object]] = []

    for process in sampled_processes:
        try:
            memory_info = process.memory_info()

            process_results.append(
                {
                    "pid": process.pid,
                    "name": process.name() or "Unknown",
                    "username": process.username() or "Unknown",
                    "cpu_percent": round(
                        process.cpu_percent(interval=None),
                        1,
                    ),
                    "memory_mb": round(
                        memory_info.rss / (1024 * 1024),
                        1,
                    ),
                }
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    top_cpu = sorted(
        process_results,
        key=lambda item: float(item["cpu_percent"]),
        reverse=True,
    )[:process_limit]

    top_memory = sorted(
        process_results,
        key=lambda item: float(item["memory_mb"]),
        reverse=True,
    )[:process_limit]

    return {
        "top_cpu": top_cpu,
        "top_memory": top_memory,
    }


def collect_system_health(
    settings: dict[str, Any],
) -> dict[str, object]:
    """Collect system, network, and process health data."""

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    network_settings = settings["network"]
    process_settings = settings.get("process_monitoring", {})

    if process_settings.get("enabled", True):
        process_data = collect_top_processes(
            process_limit=int(
                process_settings.get("process_limit", 5)
            ),
            sample_seconds=float(
                process_settings.get("sample_seconds", 1)
            ),
        )
    else:
        process_data = {
            "top_cpu": [],
            "top_memory": [],
        }

    return {
        "timestamp": datetime.now().isoformat(
            timespec="seconds"
        ),
        "hostname": socket.gethostname(),
        "operating_system": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "internet": check_internet(
            str(network_settings["internet_url"]),
            int(network_settings["timeout_seconds"]),
        ),
        "dns": check_dns(
            str(network_settings["dns_hostname"])
        ),
        "processes": process_data,
        "warnings": [],
        "comparison": {},
    }


def add_health_warnings(
    report: dict[str, object],
    thresholds: dict[str, float],
) -> None:
    """Add warnings for unhealthy system or network conditions."""

    warnings: list[str] = []

    metrics = {
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

    for metric_name, metric_values in metrics.items():
        current_value, threshold = metric_values

        if current_value >= threshold:
            warnings.append(
                f"{metric_name} usage is above the "
                f"{threshold:.0f}% threshold: "
                f"{current_value:.1f}%"
            )

    internet = report["internet"]
    dns = report["dns"]

    if not internet["reachable"]:
        warnings.append(
            f"Internet check failed: {internet['error']}"
        )

    if not dns["resolved"]:
        warnings.append(
            f"DNS resolution failed for "
            f"{dns['hostname']}: {dns['error']}"
        )

    report["warnings"] = warnings


def find_previous_report(
    report_directory: str,
) -> Path | None:
    """Find the newest existing health report."""

    output_directory = Path(report_directory)

    if not output_directory.exists():
        return None

    reports = sorted(
        output_directory.glob("health_report_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    return reports[0] if reports else None


def load_previous_report(
    report_path: Path | None,
) -> dict[str, object] | None:
    """Load the previous health report."""

    if report_path is None:
        return None

    try:
        return json.loads(
            report_path.read_text(encoding="utf-8")
        )

    except (OSError, json.JSONDecodeError):
        LOGGER.warning(
            "Unable to load previous report: %s",
            report_path,
        )
        return None


def compare_with_previous(
    report: dict[str, object],
    previous_report: dict[str, object] | None,
) -> None:
    """Compare current metrics against the previous report."""

    if previous_report is None:
        report["comparison"] = {
            "status": "No previous report available"
        }
        return

    comparison: dict[str, object] = {}

    for metric in (
        "cpu_percent",
        "memory_percent",
        "disk_percent",
    ):
        current_value = float(report[metric])
        previous_value = float(
            previous_report.get(metric, 0.0)
        )

        change = round(
            current_value - previous_value,
            1,
        )

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
    """Save a timestamped JSON health report."""

    output_directory = Path(report_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    report_path = (
        output_directory
        / f"health_report_{timestamp}.json"
    )

    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    return report_path


def format_cpu_processes(
    report: dict[str, object],
) -> list[str]:
    """Format top CPU processes for terminal and email output."""

    process_data = report["processes"]
    output_lines: list[str] = []

    for process in process_data["top_cpu"]:
        output_lines.append(
            f"- {process['name']} "
            f"(PID {process['pid']}): "
            f"{float(process['cpu_percent']):.1f}% CPU"
        )

    return output_lines or [
        "- No process data available."
    ]


def format_memory_processes(
    report: dict[str, object],
) -> list[str]:
    """Format top memory processes for terminal and email output."""

    process_data = report["processes"]
    output_lines: list[str] = []

    for process in process_data["top_memory"]:
        output_lines.append(
            f"- {process['name']} "
            f"(PID {process['pid']}): "
            f"{float(process['memory_mb']):.1f} MB"
        )

    return output_lines or [
        "- No process data available."
    ]


def build_email_body(
    report: dict[str, object],
) -> str:
    """Build the plain-text email health report."""

    internet = report["internet"]
    dns = report["dns"]
    warnings = report["warnings"]

    if internet["reachable"]:
        internet_status = (
            f"Reachable ({internet['status_code']}, "
            f"{float(internet['response_time_ms']):.1f} ms)"
        )
    else:
        internet_status = (
            f"Failed - {internet['error']}"
        )

    if dns["resolved"]:
        dns_status = (
            f"{dns['hostname']} -> {dns['ip_address']}"
        )
    else:
        dns_status = (
            f"Failed - {dns['error']}"
        )

    lines = [
        "Homelab Guardian Health Report",
        "",
        f"Hostname: {report['hostname']}",
        f"Timestamp: {report['timestamp']}",
        "",
        f"CPU Usage: {float(report['cpu_percent']):.1f}%",
        f"Memory Usage: {float(report['memory_percent']):.1f}%",
        f"Disk Usage: {float(report['disk_percent']):.1f}%",
        "",
        f"Internet: {internet_status}",
        f"DNS: {dns_status}",
        "",
        "Top CPU Processes:",
    ]

    lines.extend(format_cpu_processes(report))

    lines.extend(
        [
            "",
            "Top Memory Processes:",
        ]
    )

    lines.extend(format_memory_processes(report))

    lines.extend(
        [
            "",
            "Warnings:",
        ]
    )

    if warnings:
        lines.extend(
            f"- {warning}"
            for warning in warnings
        )
    else:
        lines.append("- No issues detected.")

    return "\n".join(lines)


def send_email_notification(
    report: dict[str, object],
    settings: dict[str, Any],
) -> None:
    """Send the health report through Gmail SMTP."""

    notification_settings = settings["notifications"]

    if not notification_settings.get(
        "email_enabled",
        False,
    ):
        LOGGER.info("Email notifications are disabled")
        return

    if (
        not report["warnings"]
        and not notification_settings.get(
            "send_healthy_reports",
            False,
        )
    ):
        LOGGER.info("Healthy email report skipped")
        return

    sender = os.getenv("GUARDIAN_EMAIL_FROM")
    recipient = os.getenv("GUARDIAN_EMAIL_TO")
    app_password = os.getenv(
        "GUARDIAN_EMAIL_APP_PASSWORD"
    )

    if not sender or not recipient or not app_password:
        raise ValueError(
            "Email environment variables are missing. "
            "Check the local .env file."
        )

    status = (
        "WARNING"
        if report["warnings"]
        else "HEALTHY"
    )

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = (
        f"Homelab Guardian: {status}"
    )
    message.set_content(build_email_body(report))

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
    ) as smtp:
        smtp.login(sender, app_password)
        smtp.send_message(message)

    LOGGER.info(
        "Email notification sent to %s",
        recipient,
    )


def display_network_health(
    report: dict[str, object],
) -> None:
    """Display internet and DNS health."""

    internet = report["internet"]
    dns = report["dns"]

    print("\nNetwork Health")
    print("-" * 60)

    if internet["reachable"]:
        print(
            "Internet:          Reachable "
            f"({internet['status_code']}, "
            f"{float(internet['response_time_ms']):.1f} ms)"
        )
    else:
        print(
            f"Internet:          Failed "
            f"({internet['error']})"
        )

    if dns["resolved"]:
        print(
            f"DNS:               "
            f"{dns['hostname']} -> "
            f"{dns['ip_address']}"
        )
    else:
        print(
            f"DNS:               Failed for "
            f"{dns['hostname']} "
            f"({dns['error']})"
        )


def display_comparison(
    report: dict[str, object],
) -> None:
    """Display changes from the previous report."""

    comparison = report["comparison"]

    print("\nComparison with Previous Report")
    print("-" * 60)

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
            f"({sign}{change:.1f}%, "
            f"{details['direction']})"
        )


def display_process_health(
    report: dict[str, object],
) -> None:
    """Display the top CPU and memory processes."""

    print("\nTop CPU Processes")
    print("-" * 60)

    for line in format_cpu_processes(report):
        print(line)

    print("\nTop Memory Processes")
    print("-" * 60)

    for line in format_memory_processes(report):
        print(line)


def display_report(
    report: dict[str, object],
    guardian_name: str,
    version: str,
) -> None:
    """Display the complete health report."""

    print("\n" + "=" * 60)
    print(f"{guardian_name:^60}")
    print(f"{f'Version {version}':^60}")
    print("=" * 60)

    print("\nSystem Information")
    print("-" * 60)
    print(f"Hostname:          {report['hostname']}")
    print(
        f"Operating System:  "
        f"{report['operating_system']}"
    )
    print(
        f"Python Version:    "
        f"{report['python_version']}"
    )
    print(
        f"Report Time:       "
        f"{report['timestamp']}"
    )

    print("\nSystem Health")
    print("-" * 60)
    print(
        f"CPU Usage:         "
        f"{float(report['cpu_percent']):.1f}%"
    )
    print(
        f"Memory Usage:      "
        f"{float(report['memory_percent']):.1f}%"
    )
    print(
        f"Disk Usage:        "
        f"{float(report['disk_percent']):.1f}%"
    )

    display_network_health(report)
    display_comparison(report)
    display_process_health(report)

    print("\nStatus")
    print("-" * 60)

    warnings = report["warnings"]

    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}")
    else:
        print(
            "All monitored system and "
            "network metrics are healthy."
        )

    print("=" * 60)


def main() -> int:
    """Run Homelab Guardian."""

    try:
        load_dotenv(dotenv_path=ENV_PATH)

        settings = load_settings()
        configure_logging(settings)

        LOGGER.info("Homelab Guardian started")

        report_directory = str(
            settings["reports"]["directory"]
        )

        previous_report = load_previous_report(
            find_previous_report(report_directory)
        )

        report = collect_system_health(settings)

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

        LOGGER.info(
            "Health report saved to %s",
            report_path,
        )

        if report["warnings"]:
            for warning in report["warnings"]:
                LOGGER.warning(warning)
        else:
            LOGGER.info(
                "All monitored system and "
                "network metrics are healthy"
            )

        send_email_notification(
            report,
            settings,
        )

        display_report(
            report,
            str(settings["guardian_name"]),
            str(settings["version"]),
        )

        print(
            f"\nReport saved to: "
            f"{report_path.resolve()}\n"
        )

        LOGGER.info(
            "Homelab Guardian completed successfully"
        )

        return 0

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        KeyError,
        OSError,
        ValueError,
        TypeError,
        smtplib.SMTPException,
    ) as error:
        LOGGER.exception("Homelab Guardian failed")

        print(
            f"Homelab Guardian failed: {error}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())