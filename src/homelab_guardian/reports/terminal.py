from __future__ import annotations

from typing import Any


SEPARATOR = "=" * 48
SECTION_SEPARATOR = "-" * 48


def _format_network_status(report: dict[str, Any]) -> tuple[str, str]:
    """Return human-readable internet and DNS status values."""

    internet = report.get("internet", {})
    dns = report.get("dns", {})

    if internet.get("reachable"):
        status_code = internet.get("status_code", "unknown")
        response_time = float(
            internet.get("response_time_ms", 0.0)
        )

        internet_status = (
            f"Reachable ({status_code}, {response_time:.1f} ms)"
        )
    else:
        internet_status = (
            f"Failed - {internet.get('error') or 'unknown error'}"
        )

    if dns.get("resolved"):
        dns_status = (
            f"{dns.get('hostname', 'unknown')} -> "
            f"{dns.get('ip_address', 'unknown')}"
        )
    else:
        dns_status = (
            f"Failed - {dns.get('error') or 'unknown error'}"
        )

    return internet_status, dns_status


def build_terminal_report(
    report: dict[str, Any],
    guardian_name: str,
    version: str,
) -> str:
    """Build the complete terminal health report."""

    health = report["health"]
    internet_status, dns_status = _format_network_status(
        report
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
        f"CPU Usage:         {float(report['cpu_percent']):.1f}%",
        f"Memory Usage:      {float(report['memory_percent']):.1f}%",
        f"Disk Usage:        {float(report['disk_percent']):.1f}%",
        "",
        "Network Health",
        SECTION_SEPARATOR,
        f"Internet:          {internet_status}",
        f"DNS:               {dns_status}",
        "",
        "Issues",
        SECTION_SEPARATOR,
    ]

    issues = health.get("issues", [])

    if issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("- No monitored issues detected.")

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