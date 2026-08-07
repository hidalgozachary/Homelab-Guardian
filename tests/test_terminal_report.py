from homelab_guardian.reports.terminal import (
    build_terminal_report,
)


def build_base_report() -> dict:
    return {
        "timestamp": "2026-08-07T13:30:00",
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


def test_build_healthy_terminal_report() -> None:
    report = build_base_report()

    output = build_terminal_report(
        report=report,
        guardian_name="Homelab Guardian",
        version="0.8.0-dev",
    )

    assert "Homelab Guardian" in output
    assert "Status:            HEALTHY" in output
    assert "Health Score:      100 / 100" in output
    assert "Hostname:          PandaServer" in output
    assert "CPU Usage:         12.5%" in output
    assert "Everything looks healthy." in output


def test_build_warning_terminal_report_lists_issues() -> None:
    report = build_base_report()

    report["health"] = {
        "status": "WARNING",
        "score": 90,
        "issues": [
            "CPU usage is above the 80% threshold: 95.0%"
        ],
        "issue_summary": (
            "CPU usage is above the 80% threshold: 95.0%"
        ),
    }

    output = build_terminal_report(
        report=report,
        guardian_name="Homelab Guardian",
        version="0.8.0-dev",
    )

    assert "Status:            WARNING" in output
    assert "Attention may be required." in output

    assert (
        "- CPU usage is above the 80% threshold: 95.0%"
        in output
    )


def test_terminal_report_includes_smart_devices() -> None:
    report = build_base_report()

    report["collectors"] = {
        "smart": {
            "status": "COLLECTED",
            "available": True,
            "data": {
                "parity": {
                    "available": True,
                    "smart": {
                        "protocol": "ATA",
                        "status": "PASSED",
                        "temperature_celsius": 39,
                        "power_on_hours": 2962,
                        "reallocated_sectors": 0,
                        "pending_sectors": 0,
                        "uncorrectable_sectors": 0,
                    },
                },
                "cache": {
                    "available": True,
                    "smart": {
                        "protocol": "NVMe",
                        "status": "PASSED",
                        "temperature_celsius": 44,
                        "power_on_hours": 3626,
                        "media_errors": 0,
                        "percentage_used": 0,
                    },
                },
            },
        }
    }

    output = build_terminal_report(
        report=report,
        guardian_name="Homelab Guardian",
        version="0.8.0-dev",
    )

    assert "SMART Health" in output

    assert "Parity" in output
    assert "Protocol:         ATA" in output
    assert "Temperature:      39°C" in output
    assert "Power-On Hours:   2962" in output

    assert "Cache" in output
    assert "Protocol:         NVMe" in output
    assert "Temperature:      44°C" in output
    assert "Media Errors:     0" in output
    assert "Endurance Used:   0%" in output


def test_terminal_report_includes_docker_summary() -> None:
    report = build_base_report()

    report["collectors"] = {
        "docker": {
            "status": "COLLECTED",
            "available": True,
            "data": {
                "summary": {
                    "total": 2,
                    "running": 2,
                    "stopped": 0,
                    "healthy": 2,
                    "unhealthy": 0,
                    "restarting": 0,
                    "paused": 0,
                },
                "containers": [],
            },
        }
    }

    output = build_terminal_report(
        report=report,
        guardian_name="Homelab Guardian",
        version="0.8.0-dev",
    )

    assert "Docker" in output
    assert "Total:             2" in output
    assert "Running:           2" in output
    assert "Healthy:           2" in output
    assert "Unhealthy:         0" in output


def test_terminal_report_includes_docker_containers() -> None:
    report = build_base_report()

    report["collectors"] = {
        "docker": {
            "status": "COLLECTED",
            "available": True,
            "data": {
                "summary": {
                    "total": 2,
                    "running": 2,
                    "stopped": 0,
                    "healthy": 2,
                    "unhealthy": 0,
                    "restarting": 0,
                    "paused": 0,
                },
                "containers": [
                    {
                        "name": "UptimeKuma",
                        "state": "running",
                        "health": "healthy",
                        "restart_count": 0,
                        "exit_code": 0,
                    },
                    {
                        "name": "pihole",
                        "state": "running",
                        "health": "healthy",
                        "restart_count": 0,
                        "exit_code": 0,
                    },
                ],
            },
        }
    }

    output = build_terminal_report(
        report=report,
        guardian_name="Homelab Guardian",
        version="0.8.0-dev",
    )

    assert "Containers" in output
    assert "UptimeKuma" in output
    assert "pihole" in output
    assert "State:            running" in output
    assert "Health:           healthy" in output
    assert "Restart Count:    0" in output
    assert "Exit Code:        0" in output