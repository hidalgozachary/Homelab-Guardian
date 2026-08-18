from __future__ import annotations

from typing import Any


SEPARATOR = "=" * 48
SECTION_SEPARATOR = "-" * 48


def _format_network_status(
    report: dict[str, Any],
) -> tuple[str, str]:
    """Return human-readable internet and DNS status values."""

    internet = report.get("internet", {})
    dns = report.get("dns", {})

    if internet.get("reachable"):
        status_code = internet.get(
            "status_code",
            "unknown",
        )

        response_time = float(
            internet.get(
                "response_time_ms",
                0.0,
            )
        )

        internet_status = (
            f"Reachable "
            f"({status_code}, {response_time:.1f} ms)"
        )
    else:
        internet_status = (
            "Failed - "
            f"{internet.get('error') or 'unknown error'}"
        )

    if dns.get("resolved"):
        dns_status = (
            f"{dns.get('hostname', 'unknown')} -> "
            f"{dns.get('ip_address', 'unknown')}"
        )
    else:
        dns_status = (
            "Failed - "
            f"{dns.get('error') or 'unknown error'}"
        )

    return internet_status, dns_status


def _format_smart_section(
    report: dict[str, Any],
) -> list[str]:
    """Return formatted SMART collector lines."""

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

    if not isinstance(smart_collector, dict):
        return []

    if smart_collector.get("status") != "COLLECTED":
        return []

    devices = smart_collector.get(
        "data",
        {},
    )

    if not isinstance(devices, dict):
        return []

    if not devices:
        return []

    lines = [
        "",
        "SMART Health",
        SECTION_SEPARATOR,
    ]

    for device_name, device_result in devices.items():
        if not isinstance(device_result, dict):
            continue

        if not device_result.get(
            "available",
            False,
        ):
            continue

        smart = device_result.get(
            "smart",
        )

        if not isinstance(smart, dict):
            continue

        label = (
            device_name
            .replace("_", " ")
            .title()
        )

        protocol = (
            smart.get("protocol")
            or "unknown"
        )

        status = (
            smart.get("status")
            or "UNKNOWN"
        )

        temperature = smart.get(
            "temperature_celsius"
        )

        power_on_hours = smart.get(
            "power_on_hours"
        )

        temperature_text = (
            f"{temperature}°C"
            if isinstance(
                temperature,
                (int, float),
            )
            else "N/A"
        )

        hours_text = (
            str(power_on_hours)
            if isinstance(
                power_on_hours,
                (int, float),
            )
            else "N/A"
        )

        lines.extend(
            [
                f"{label}",
                f"  Protocol:         {protocol}",
                f"  Health:           {status}",
                f"  Temperature:      {temperature_text}",
                f"  Power-On Hours:   {hours_text}",
            ]
        )

        if protocol == "ATA":
            reallocated = smart.get(
                "reallocated_sectors"
            )
            pending = smart.get(
                "pending_sectors"
            )
            uncorrectable = smart.get(
                "uncorrectable_sectors"
            )

            lines.extend(
                [
                    (
                        "  Reallocated:      "
                        f"{reallocated if reallocated is not None else 'N/A'}"
                    ),
                    (
                        "  Pending:          "
                        f"{pending if pending is not None else 'N/A'}"
                    ),
                    (
                        "  Uncorrectable:    "
                        f"{uncorrectable if uncorrectable is not None else 'N/A'}"
                    ),
                ]
            )

        elif protocol == "NVMe":
            media_errors = smart.get(
                "media_errors"
            )
            percentage_used = smart.get(
                "percentage_used"
            )

            lines.extend(
                [
                    (
                        "  Media Errors:     "
                        f"{media_errors if media_errors is not None else 'N/A'}"
                    ),
                    (
                        "  Endurance Used:   "
                        f"{percentage_used}%"
                        if percentage_used is not None
                        else "  Endurance Used:   N/A"
                    ),
                ]
            )

        lines.append("")

    if lines[-1] == "":
        lines.pop()

    return lines


def _format_kernel_health_section(
    report: dict[str, Any],
) -> list[str]:
    """Return formatted kernel-health collector lines."""

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

    if not isinstance(kernel_collector, dict):
        return []

    status = kernel_collector.get(
        "status",
        "UNAVAILABLE",
    )

    if status != "COLLECTED":
        data = kernel_collector.get(
            "data",
            {},
        )

        data_error = (
            data.get("error")
            if isinstance(data, dict)
            else None
        )

        error = (
            kernel_collector.get("error")
            or data_error
            or "Kernel health data unavailable"
        )

        return [
            "",
            "Kernel Health",
            SECTION_SEPARATOR,
            "Status:            UNAVAILABLE",
            f"Error:             {error}",
        ]

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
        counts = {}

    total_events = data.get(
        "total_events",
        0,
    )

    try:
        total_events = int(
            total_events
        )
    except (TypeError, ValueError):
        total_events = 0

    kernel_status = (
        "HEALTHY"
        if total_events == 0
        else "ATTENTION"
    )

    return [
        "",
        "Kernel Health",
        SECTION_SEPARATOR,
        f"Status:            {kernel_status}",
        f"Detected Events:   {total_events}",
        (
            "Kernel Faults:     "
            f"{counts.get('kernel_fault', 0)}"
        ),
        (
            "Hardware Errors:   "
            f"{counts.get('hardware_error', 0)}"
        ),
        (
            "RCU Stalls:        "
            f"{counts.get('rcu_stall', 0)}"
        ),
        (
            "OOM Events:        "
            f"{counts.get('oom', 0)}"
        ),
        (
            "BTRFS Errors:      "
            f"{counts.get('btrfs_error', 0)}"
        ),
        (
            "XFS Errors:        "
            f"{counts.get('xfs_error', 0)}"
        ),
        (
            "I/O Errors:        "
            f"{counts.get('io_error', 0)}"
        ),
        (
            "NVMe Errors:       "
            f"{counts.get('nvme_error', 0)}"
        ),
        (
            "Disk Resets:       "
            f"{counts.get('disk_reset', 0)}"
        ),
    ]


def _format_docker_section(
    report: dict[str, Any],
) -> list[str]:
    """Return formatted Docker collector lines."""

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

    if not isinstance(docker_collector, dict):
        return []

    if docker_collector.get("status") != "COLLECTED":
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
        "",
        "Docker",
        SECTION_SEPARATOR,
        f"Total:             {summary.get('total', 0)}",
        f"Running:           {summary.get('running', 0)}",
        f"Stopped:           {summary.get('stopped', 0)}",
        f"Healthy:           {summary.get('healthy', 0)}",
        f"Unhealthy:         {summary.get('unhealthy', 0)}",
        f"Restarting:        {summary.get('restarting', 0)}",
        f"Paused:            {summary.get('paused', 0)}",
    ]

    if containers:
        lines.extend(
            [
                "",
                "Containers",
                SECTION_SEPARATOR,
            ]
        )

    for container in containers:
        if not isinstance(container, dict):
            continue

        name = (
            container.get("name")
            or "Unnamed container"
        )

        state = (
            container.get("state")
            or "unknown"
        )

        health = (
            container.get("health")
            or "not reported"
        )

        restart_count = container.get(
            "restart_count"
        )

        exit_code = container.get(
            "exit_code"
        )

        restart_text = (
            str(restart_count)
            if restart_count is not None
            else "N/A"
        )

        exit_text = (
            str(exit_code)
            if exit_code is not None
            else "N/A"
        )

        lines.extend(
            [
                f"{name}",
                f"  State:            {state}",
                f"  Health:           {health}",
                f"  Restart Count:    {restart_text}",
                f"  Exit Code:        {exit_text}",
                "",
            ]
        )

    if lines[-1] == "":
        lines.pop()

    return lines


def build_terminal_report(
    report: dict[str, Any],
    guardian_name: str,
    version: str,
) -> str:
    """Build the complete terminal health report."""

    health = report["health"]

    internet_status, dns_status = (
        _format_network_status(
            report
        )
    )

    lines = [
        SEPARATOR,
        f"{guardian_name:^48}",
        f"{f'Version {version}':^48}",
        SEPARATOR,
        "",
        "Overall Health",
        SECTION_SEPARATOR,
        f"Status:            {health['status']}",
        f"Health Score:      {health['score']} / 100",
        "",
        "System Information",
        SECTION_SEPARATOR,
        f"Hostname:          {report['hostname']}",
        f"Operating System:  {report['operating_system']}",
        f"Python Version:    {report['python_version']}",
        f"Timestamp:         {report['timestamp']}",
        "",
        "System Health",
        SECTION_SEPARATOR,
        (
            "CPU Usage:         "
            f"{float(report['cpu_percent']):.1f}%"
        ),
        (
            "Memory Usage:      "
            f"{float(report['memory_percent']):.1f}%"
        ),
        (
            "Disk Usage:        "
            f"{float(report['disk_percent']):.1f}%"
        ),
        "",
        "Network Health",
        SECTION_SEPARATOR,
        f"Internet:          {internet_status}",
        f"DNS:               {dns_status}",
    ]

    lines.extend(
        _format_smart_section(
            report
        )
    )

    lines.extend(
        _format_kernel_health_section(
            report
        )
    )

    lines.extend(
        _format_docker_section(
            report
        )
    )

    lines.extend(
        [
            "",
            "Issues",
            SECTION_SEPARATOR,
        ]
    )

    issues = health.get(
        "issues",
        [],
    )

    if issues:
        lines.extend(
            f"- {issue}"
            for issue in issues
        )
    else:
        lines.append(
            "- No monitored issues detected."
        )

    lines.extend(
        [
            "",
            SEPARATOR,
            (
                "Everything looks healthy."
                if health["status"] == "HEALTHY"
                else "Attention may be required."
            ),
            SEPARATOR,
        ]
    )

    return "\n".join(lines)


def print_terminal_report(
    report: dict[str, Any],
    guardian_name: str,
    version: str,
) -> None:
    """Print the formatted terminal report."""

    print(
        build_terminal_report(
            report=report,
            guardian_name=guardian_name,
            version=version,
        )
    )