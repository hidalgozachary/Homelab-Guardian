from homelab_guardian.reports.terminal import (
    build_terminal_report,
)


def test_build_healthy_terminal_report() -> None:
    report = {
        "timestamp": "2026-08-05T14:30:00",
        "hostname": "PandaServer",
        "operating_system": "Unraid 7.3.2",
        "python_version": "3.11.9",
        "cpu_percent": 12.5,
        "memory_percent": 5.0,
        "disk_percent": 2.0,
        "internet": {
            "reachable": True,
            "status_code": 200,
            "response_time_ms": 25.4,
            "error": None,
        },
        "dns": {
            "resolved": True,
            "hostname": "cloudflare.com",
            "ip_address": "104.16.132.229",
            "error": None,
        },
        "health": {
            "status": "HEALTHY",
            "score": 100,
            "issues": [],
            "issue_summary": (
                "No monitored issues detected."
            ),
        },
    }

    output = build_terminal_report(
        report=report,
        guardian_name="Homelab Guardian",
        version="0.7.0-dev",
    )

    assert "Homelab Guardian" in output
    assert "Status:            HEALTHY" in output
    assert "Health Score:      100 / 100" in output
    assert "Hostname:          PandaServer" in output
    assert "CPU Usage:         12.5%" in output
    assert "Everything looks healthy." in output


def test_build_warning_terminal_report_lists_issues() -> None:
    report = {
        "timestamp": "2026-08-05T14:30:00",
        "hostname": "PandaServer",
        "operating_system": "Unraid 7.3.2",
        "python_version": "3.11.9",
        "cpu_percent": 95.0,
        "memory_percent": 5.0,
        "disk_percent": 2.0,
        "internet": {
            "reachable": True,
            "status_code": 200,
            "response_time_ms": 25.4,
            "error": None,
        },
        "dns": {
            "resolved": True,
            "hostname": "cloudflare.com",
            "ip_address": "104.16.132.229",
            "error": None,
        },
        "health": {
            "status": "WARNING",
            "score": 90,
            "issues": [
                "CPU usage is above the 80% threshold: 95.0%"
            ],
            "issue_summary": (
                "CPU usage is above the 80% threshold: 95.0%"
            ),
        },
    }

    output = build_terminal_report(
        report=report,
        guardian_name="Homelab Guardian",
        version="0.7.0-dev",
    )

    assert "Status:            WARNING" in output
    assert "Attention may be required." in output
    assert (
        "- CPU usage is above the 80% threshold: 95.0%"
        in output
    )