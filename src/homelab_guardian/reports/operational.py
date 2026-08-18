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


def _format_timestamp(
    timestamp: str,
) -> tuple[str, str]:
    """Return friendly date and time values."""

    try:
        parsed = datetime.fromisoformat(
            timestamp
        )
    except (TypeError, ValueError):
        return (
            str(timestamp or "Unavailable"),
            "Unavailable",
        )

    report_date = parsed.strftime(
        "%A, %B %d, %Y"
    )

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


def _format_temperature(
    value: object,
) -> str:
    """Format a Celsius temperature."""

    if value is None:
        return "N/A"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    return f"{number:.0f}°C"


def _format_cpu_temperature(
    report: dict[str, Any],
) -> str:
    """Return CPU temperature from available report data."""

    temperature = report.get(
        "cpu_temperature"
    )

    if temperature is None:
        collectors = report.get(
            "collectors",
            {},
        )

        if isinstance(collectors, dict):
            host = collectors.get(
                "host",
                {},
            )

            if isinstance(host, dict):
                data = host.get(
                    "data",
                    {},
                )

                if isinstance(data, dict):
                    temperature = data.get(
                        "cpu_temperature"
                    )

                    if temperature is None:
                        cpu_data = data.get(
                            "cpu",
                            {},
                        )

                        if isinstance(cpu_data, dict):
                            temperature = cpu_data.get(
                                "temperature_celsius"
                            )

    if temperature is None:
        return "Unavailable"

    try:
        return f"{float(temperature):.1f}°C"
    except (TypeError, ValueError):
        return str(temperature)


def _format_load_average(
    report: dict[str, Any],
) -> str:
    """Return the primary load-average value."""

    load_average = report.get(
        "load_average"
    )

    if load_average is None:
        collectors = report.get(
            "collectors",
            {},
        )

        if isinstance(collectors, dict):
            host = collectors.get(
                "host",
                {},
            )

            if isinstance(host, dict):
                data = host.get(
                    "data",
                    {},
                )

                if isinstance(data, dict):
                    load_average = data.get(
                        "load_average"
                    )

    if load_average is None:
        return "Unavailable"

    if isinstance(
        load_average,
        (list, tuple),
    ):
        if not load_average:
            return "Unavailable"

        load_average = load_average[0]

    try:
        return f"{float(load_average):.2f}"
    except (TypeError, ValueError):
        return str(load_average)


def _format_uptime(
    report: dict[str, Any],
) -> str:
    """Return a friendly uptime value."""

    uptime = report.get("uptime")

    if uptime:
        return str(uptime)

    collectors = report.get(
        "collectors",
        {},
    )

    if isinstance(collectors, dict):
        host = collectors.get(
            "host",
            {},
        )

        if isinstance(host, dict):
            data = host.get(
                "data",
                {},
            )

            if isinstance(data, dict):
                uptime = data.get(
                    "uptime"
                )

                if uptime:
                    return str(uptime)

    return "Unavailable"


def _format_storage(
    report: dict[str, Any],
) -> tuple[str, str]:
    """Return array and cache usage with collector fallback."""

    storage = report.get(
        "storage"
    )

    if isinstance(storage, dict):
        array_usage = _format_percent(
            storage.get(
                "array_percent"
            ),
            decimal_places=0,
        )

        cache_usage = _format_percent(
            storage.get(
                "cache_percent"
            ),
            decimal_places=0,
        )

        return (
            array_usage,
            cache_usage,
        )

    collectors = report.get(
        "collectors",
        {},
    )

    if not isinstance(collectors, dict):
        return (
            "Not collected",
            "Not collected",
        )

    storage_collector = collectors.get(
        "storage",
        {},
    )

    if not isinstance(
        storage_collector,
        dict,
    ):
        return (
            "Not collected",
            "Not collected",
        )

    if (
        storage_collector.get("status")
        != "COLLECTED"
    ):
        return (
            "Not collected",
            "Not collected",
        )

    data = storage_collector.get(
        "data",
        {},
    )

    if not isinstance(data, dict):
        return (
            "Not collected",
            "Not collected",
        )

    array_data = data.get(
        "array",
        {},
    )

    cache_data = data.get(
        "cache",
        {},
    )

    array_usage = (
        _format_percent(
            array_data.get("percent"),
            decimal_places=0,
        )
        if isinstance(array_data, dict)
        else "Not collected"
    )

    cache_usage = (
        _format_percent(
            cache_data.get("percent"),
            decimal_places=0,
        )
        if isinstance(cache_data, dict)
        else "Not collected"
    )

    return (
        array_usage,
        cache_usage,
    )


def _format_legacy_docker(
    report: dict[str, Any],
) -> tuple[str, str, str]:
    """Return Docker counts for legacy report data."""

    docker = report.get(
        "docker"
    )

    if not isinstance(docker, dict):
        return (
            "Not collected",
            "Not collected",
            "Not collected",
        )

    return (
        str(
            docker.get(
                "running_count",
                0,
            )
        ),
        str(
            docker.get(
                "stopped_count",
                0,
            )
        ),
        str(
            docker.get(
                "unhealthy_count",
                0,
            )
        ),
    )


def _format_smart_lines(
    report: dict[str, Any],
) -> list[str]:
    """Return compact SMART report lines."""

    collectors = report.get(
        "collectors",
        {},
    )

    if not isinstance(collectors, dict):
        return []

    smart_collector = collectors.get(
        "smart",
        {},
    )

    if not isinstance(
        smart_collector,
        dict,
    ):
        return []

    if (
        smart_collector.get("status")
        != "COLLECTED"
    ):
        return []

    devices = smart_collector.get(
        "data",
        {},
    )

    if not isinstance(devices, dict):
        return []

    lines: list[str] = [
        "💾 SMART",
    ]

    device_count = 0

    for device_name, device_result in devices.items():
        if not isinstance(
            device_result,
            dict,
        ):
            continue

        if not device_result.get(
            "available",
            False,
        ):
            continue

        smart = device_result.get(
            "smart"
        )

        if not isinstance(smart, dict):
            continue

        device_count += 1

        label = (
            device_name
            .replace("_", " ")
            .title()
        )

        status = str(
            smart.get(
                "status",
                "UNKNOWN",
            )
        )

        temperature = (
            _format_temperature(
                smart.get(
                    "temperature_celsius"
                )
            )
        )

        lines.append(
            f"{label:<12} : "
            f"{status} | {temperature}"
        )

    if device_count == 0:
        return []

    lines.append("")

    return lines


def _format_kernel_lines(
    report: dict[str, Any],
) -> list[str]:
    """Return compact kernel-health report lines."""

    collectors = report.get(
        "collectors",
        {},
    )

    if not isinstance(collectors, dict):
        return []

    kernel_collector = collectors.get(
        "kernel_health",
        {},
    )

    if not isinstance(
        kernel_collector,
        dict,
    ):
        return []

    if (
        kernel_collector.get("status")
        != "COLLECTED"
    ):
        return []

    data = kernel_collector.get(
        "data",
        {},
    )

    if not isinstance(data, dict):
        return []

    counts = data.get(
        "counts",
        {},
    )

    if not isinstance(counts, dict):
        return []

    try:
        total_events = int(
            data.get(
                "total_events",
                0,
            )
        )
    except (TypeError, ValueError):
        total_events = 0

    status = (
        "HEALTHY"
        if total_events == 0
        else "ATTENTION"
    )

    return [
        "🧠 KERNEL HEALTH",
        f"Status       : {status}",
        f"Events       : {total_events}",
        (
            "Faults       : "
            f"{counts.get('kernel_fault', 0)}"
        ),
        (
            "Hardware     : "
            f"{counts.get('hardware_error', 0)}"
        ),
        (
            "OOM          : "
            f"{counts.get('oom', 0)}"
        ),
        (
            "I/O Errors   : "
            f"{counts.get('io_error', 0)}"
        ),
        (
            "NVMe Errors  : "
            f"{counts.get('nvme_error', 0)}"
        ),
        "",
    ]


def _container_icon(
    container: dict[str, Any],
) -> str:
    """Return an icon representing container health."""

    state = container.get("state")
    health = container.get("health")

    if health == "unhealthy":
        return "❌"

    if state == "restarting":
        return "⚠️"

    if state == "exited":
        return "⚠️"

    if state == "running":
        return "✅"

    return "ℹ️"


def _format_docker_lines(
    report: dict[str, Any],
) -> list[str]:
    """Return compact Docker report lines."""

    collectors = report.get(
        "collectors",
        {},
    )

    if not isinstance(collectors, dict):
        return []

    docker_collector = collectors.get(
        "docker",
        {},
    )

    if not isinstance(
        docker_collector,
        dict,
    ):
        return []

    if (
        docker_collector.get("status")
        != "COLLECTED"
    ):
        return []

    data = docker_collector.get(
        "data",
        {},
    )

    if not isinstance(data, dict):
        return []

    summary = data.get(
        "summary",
        {},
    )

    containers = data.get(
        "containers",
        [],
    )

    if not isinstance(summary, dict):
        summary = {}

    if not isinstance(containers, list):
        containers = []

    lines = [
        "🐳 DOCKER",
        (
            "Running      : "
            f"{summary.get('running', 0)}"
        ),
        (
            "Healthy      : "
            f"{summary.get('healthy', 0)}"
        ),
        (
            "Unhealthy    : "
            f"{summary.get('unhealthy', 0)}"
        ),
        (
            "Restarting   : "
            f"{summary.get('restarting', 0)}"
        ),
    ]

    if containers:
        lines.extend(
            [
                "",
                "Containers",
            ]
        )

    for container in containers:
        if not isinstance(
            container,
            dict,
        ):
            continue

        name = str(
            container.get("name")
            or "Unnamed"
        )

        state = str(
            container.get("state")
            or "unknown"
        )

        health = (
            container.get("health")
            or "not reported"
        )

        restart_delta = container.get(
            "restart_delta"
        )

        icon = _container_icon(
            container
        )

        container_line = (
            f"{icon} {name:<12} : "
            f"{state} | {health}"
        )

        if (
            isinstance(restart_delta, int)
            and restart_delta > 0
        ):
            container_line += (
                f" | +{restart_delta} restart(s)"
            )

        lines.append(
            container_line
        )

    lines.append("")

    return lines


def _format_issue_section(
    status: str,
    issues: list[str],
) -> list[str]:
    """Build the health-summary section."""

    presentation = STATUS_PRESENTATION.get(
        status,
        {
            "status_icon": "⚪",
            "summary_icon": "ℹ️",
            "summary_heading": (
                "Health status is unknown."
            ),
            "summary_detail": (
                "Review the report."
            ),
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
        lines.extend(
            f"• {issue}"
            for issue in issues
        )
    else:
        lines.append(
            str(
                presentation[
                    "summary_detail"
                ]
            )
        )

    lines.append(
        SEPARATOR
    )

    return lines


def build_operational_report(
    report: dict[str, Any],
    report_title: str,
    version: str,
) -> str:
    """Build shared Discord and email report."""

    health = report.get(
        "health",
        {},
    )

    status = str(
        health.get(
            "status",
            "UNKNOWN",
        )
    )

    score = int(
        health.get(
            "score",
            0,
        )
    )

    issues = list(
        health.get(
            "issues",
            [],
        )
    )

    presentation = STATUS_PRESENTATION.get(
        status,
        {
            "status_icon": "⚪",
        },
    )

    report_date, report_time = (
        _format_timestamp(
            str(
                report.get(
                    "timestamp",
                    "",
                )
            )
        )
    )

    array_usage, cache_usage = (
        _format_storage(
            report
        )
    )

    legacy_running, legacy_stopped, legacy_unhealthy = (
        _format_legacy_docker(
            report
        )
    )

    lines = [
        SEPARATOR,
        f"🐼 {report_title}",
        SEPARATOR,
        "",
        (
            f"{presentation['status_icon']} "
            "OVERALL HEALTH"
        ),
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
            "Disk Usage   : "
            f"{_format_percent(report.get('disk_percent'))}"
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
    ]

    collectors = report.get(
        "collectors",
        {},
    )

    has_collector_docker = (
        isinstance(collectors, dict)
        and isinstance(
            collectors.get("docker"),
            dict,
        )
        and collectors["docker"].get(
            "status"
        )
        == "COLLECTED"
    )

    if not has_collector_docker:
        lines.extend(
            [
                "🐳 DOCKER",
                f"Running      : {legacy_running}",
                f"Stopped      : {legacy_stopped}",
                f"Unhealthy    : {legacy_unhealthy}",
                "",
            ]
        )

    lines.extend(
        _format_smart_lines(
            report
        )
    )

    lines.extend(
        _format_kernel_lines(
            report
        )
    )

    lines.extend(
        _format_docker_lines(
            report
        )
    )

    lines.extend(
        [
            "🌐 NETWORK",
        ]
    )

    internet = report.get(
        "internet",
        {},
    )

    dns = report.get(
        "dns",
        {},
    )

    if isinstance(internet, dict):
        internet_text = (
            "Reachable"
            if internet.get(
                "reachable"
            )
            else "Unavailable"
        )
    else:
        internet_text = "Unavailable"

    if isinstance(dns, dict):
        dns_text = (
            "Resolved"
            if dns.get(
                "resolved"
            )
            else "Unavailable"
        )
    else:
        dns_text = "Unavailable"

    lines.extend(
        [
            f"Internet     : {internet_text}",
            f"DNS          : {dns_text}",
            "",
            "📊 UPTIME",
            _format_uptime(
                report
            ),
            "",
        ]
    )

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

    return "\n".join(
        lines
    )