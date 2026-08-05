from __future__ import annotations

from datetime import datetime
from typing import Any


SEPARATOR = "=" * 40

STATUS_PRESENTATION = {
    "HEALTHY": {
        "status_icon": "🟢",
        "summary_icon": "✅",
        "summary_heading": "Everything looks healthy.",
        "summary_detail": "No action required.",
    },
    "WARNING": {
        "status_icon": "🟡",
        "summary_icon": "⚠️",
        "summary_heading": "Attention may be required.",
        "summary_detail": "Review the reported issues.",
    },
    "CRITICAL": {
        "status_icon": "🔴",
        "summary_icon": "🚨",
        "summary_heading": "Immediate action required.",
        "summary_detail": "Review the reported issues immediately.",
    },
}


def _format_timestamp(timestamp: str) -> tuple[str, str]:
    """Return friendly date and time values from an ISO timestamp."""

    try:
        parsed = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return str(timestamp or "Unavailable"), "Unavailable"

    report_date = parsed.strftime("%A, %B %d, %Y")
    report_time = parsed.astimezone().strftime(
        "%-I:%M %p %Z"
    )

    return report_date, report_time


def _format_percent(
    value: object,
    decimal_places: int = 1,
) -> str:
    """Format a percentage or return Unavailable."""

    if value is None:
        return "Unavailable"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return "Unavailable"

    return f"{number:.{decimal_places}f}%"


def _format_temperature(value: object) -> str:
    """Format a Celsius temperature or return Unavailable."""

    if value is None:
        return "Unavailable"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    return f"{number:.1f}°C"


def _format_uptime(report: dict[str, Any]) -> str:
    """Return a friendly uptime value."""

    uptime = report.get("uptime")

    if uptime:
        return str(uptime)

    system = report.get("system", {})

    if isinstance(system, dict) and system.get("uptime"):
        return str(system["uptime"])

    return "Unavailable"


def _format_load_average(report: dict[str, Any]) -> str:
    """Return the primary load-average value."""

    load_average = report.get("load_average")

    if load_average is None:
        system = report.get("system", {})

        if isinstance(system, dict):
            load_average = system.get("load_average")

    if load_average is None:
        return "Unavailable"

    if isinstance(load_average, (list, tuple)):
        if not load_average:
            return "Unavailable"

        load_average = load_average[0]

    try:
        return f"{float(load_average):.2f}"
    except (TypeError, ValueError):
        return str(load_average)


def _format_cpu_temperature(
    report: dict[str, Any],
) -> str:
    """Return CPU temperature from present or future collectors."""

    cpu_temperature = report.get("cpu_temperature")

    if cpu_temperature is None:
        system = report.get("system", {})

        if isinstance(system, dict):
            cpu_temperature = system.get("cpu_temperature")

    return _format_temperature(cpu_temperature)


def _format_storage(
    report: dict[str, Any],
) -> tuple[str, str]:
    """Return array and cache usage values."""

    storage = report.get("storage")

    if not isinstance(storage, dict):
        return "Not collected", "Not collected"

    array_usage = _format_percent(
        storage.get("array_percent"),
        decimal_places=0,
    )
    cache_usage = _format_percent(
        storage.get("cache_percent"),
        decimal_places=0,
    )

    return array_usage, cache_usage


def _format_docker(
    report: dict[str, Any],
) -> tuple[str, str, str]:
    """Return Docker container totals."""

    docker = report.get("docker")

    if not isinstance(docker, dict):
        return (
            "Not collected",
            "Not collected",
            "Not collected",
        )

    running = str(docker.get("running_count", 0))
    stopped = str(docker.get("stopped_count", 0))
    unhealthy = str(docker.get("unhealthy_count", 0))

    return running, stopped, unhealthy


def _format_issue_section(
    status: str,
    issues: list[str],
) -> list[str]:
    """Build the final health-summary section."""

    presentation = STATUS_PRESENTATION.get(
        status,
        {
            "status_icon": "⚪",
            "summary_icon": "ℹ️",
            "summary_heading": "Health status is unknown.",
            "summary_detail": "Review the report.",
        },
    )

    lines = [
        SEPARATOR,
        (
            f"{presentation['summary_icon']} "
            f"{presentation['summary_heading']}"
        ),
    ]

    if issues:
        lines.extend(f"• {issue}" for issue in issues)
    else:
        lines.append(str(presentation["summary_detail"]))

    lines.append(SEPARATOR)

    return lines


def build_operational_report(
    report: dict[str, Any],
    report_title: str,
    version: str,
) -> str:
    """Build the shared operational report for Discord and Gmail."""

    health = report.get("health", {})
    status = str(health.get("status", "UNKNOWN"))
    score = int(health.get("score", 0))
    issues = list(health.get("issues", []))

    presentation = STATUS_PRESENTATION.get(
        status,
        {
            "status_icon": "⚪",
        },
    )

    report_date, report_time = _format_timestamp(
        str(report.get("timestamp", ""))
    )

    array_usage, cache_usage = _format_storage(report)

    docker_running, docker_stopped, docker_unhealthy = (
        _format_docker(report)
    )

    lines = [
        SEPARATOR,
        f"🐼 {report_title}",
        SEPARATOR,
        "",
        f"{presentation['status_icon']} OVERALL HEALTH",
        f"Health Score : {score} / 100",
        f"Status       : {status}",
        "",
        "🕒 REPORT",
        f"Generated    : {report_date}",
        f"Time         : {report_time}",
        "",
        "🖥 SYSTEM",
        (
            "CPU Temp     : "
            f"{_format_cpu_temperature(report)}"
        ),
        (
            "CPU Usage    : "
            f"{_format_percent(report.get('cpu_percent'))}"
        ),
        (
            "RAM Usage    : "
            f"{_format_percent(report.get('memory_percent'))}"
        ),
        (
            "Load Average : "
            f"{_format_load_average(report)}"
        ),
        "",
        "💾 STORAGE",
        f"Array Usage  : {array_usage}",
        f"Cache Usage  : {cache_usage}",
        "",
        "🐳 DOCKER",
        f"Running      : {docker_running}",
        f"Stopped      : {docker_stopped}",
        f"Unhealthy    : {docker_unhealthy}",
        "",
        "📊 UPTIME",
        _format_uptime(report),
        "",
    ]

    lines.extend(
        _format_issue_section(
            status=status,
            issues=issues,
        )
    )

    lines.extend(
        [
            "",
            f"Homelab Guardian v{version}",
        ]
    )

    return "\n".join(lines)