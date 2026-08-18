from homelab_guardian.reports.discord import (
    DISCORD_COLORS,
    build_discord_payload,
)


def build_base_report() -> dict:
    return {
        "timestamp": "2026-08-07T14:30:00-04:00",
        "cpu_percent": 12.5,
        "memory_percent": 15.0,
        "disk_percent": 20.0,
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
        },
    }


def test_healthy_discord_payload_uses_green_embed() -> None:
    report = build_base_report()

    payload = build_discord_payload(
        report=report,
        report_title=(
            "PandaServer Operational Report"
        ),
        version="0.8.0",
    )

    embed = payload["embeds"][0]

    assert (
        payload["username"]
        == "Homelab Guardian"
    )

    assert (
        embed["title"]
        == (
            "HEALTHY - "
            "PandaServer Operational Report"
        )
    )

    assert (
        embed["color"]
        == DISCORD_COLORS["HEALTHY"]
    )

    assert (
        "🐼 PandaServer Operational Report"
        in embed["description"]
    )


def test_critical_discord_payload_uses_red_embed() -> None:
    report = build_base_report()

    report["health"] = {
        "status": "CRITICAL",
        "score": 20,
        "issues": [
            "Disk 1 reports SMART overall health failure",
        ],
    }

    payload = build_discord_payload(
        report=report,
        report_title=(
            "PandaServer Operational Report"
        ),
        version="0.8.0",
    )

    embed = payload["embeds"][0]

    assert (
        embed["color"]
        == DISCORD_COLORS["CRITICAL"]
    )

    assert (
        "🔴 OVERALL HEALTH"
        in embed["description"]
    )

    assert (
        "• Disk 1 reports SMART overall health failure"
        in embed["description"]
    )


def test_discord_report_includes_smart_summary() -> None:
    report = build_base_report()

    report["collectors"] = {
        "smart": {
            "status": "COLLECTED",
            "available": True,
            "data": {
                "parity": {
                    "available": True,
                    "smart": {
                        "status": "PASSED",
                        "temperature_celsius": 39,
                    },
                },
                "disk1": {
                    "available": True,
                    "smart": {
                        "status": "PASSED",
                        "temperature_celsius": 38,
                    },
                },
                "cache": {
                    "available": True,
                    "smart": {
                        "status": "PASSED",
                        "temperature_celsius": 44,
                    },
                },
            },
        }
    }

    payload = build_discord_payload(
        report=report,
        report_title=(
            "PandaServer Operational Report"
        ),
        version="0.8.0",
    )

    description = (
        payload["embeds"][0]["description"]
    )

    assert "💾 SMART" in description
    assert "Parity" in description
    assert "PASSED | 39°C" in description
    assert "Disk1" in description
    assert "PASSED | 38°C" in description
    assert "Cache" in description
    assert "PASSED | 44°C" in description


def test_discord_report_includes_docker_summary() -> None:
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

    payload = build_discord_payload(
        report=report,
        report_title=(
            "PandaServer Operational Report"
        ),
        version="0.8.0",
    )

    description = (
        payload["embeds"][0]["description"]
    )

    assert "🐳 DOCKER" in description
    assert "Running      : 2" in description
    assert "Healthy      : 2" in description
    assert "Unhealthy    : 0" in description

    assert (
        "✅ UptimeKuma"
        in description
    )

    assert (
        "✅ pihole"
        in description
    )


def test_discord_report_marks_bad_container() -> None:
    report = build_base_report()

    report["health"] = {
        "status": "WARNING",
        "score": 90,
        "issues": [
            "Docker container pihole is unhealthy",
        ],
    }

    report["collectors"] = {
        "docker": {
            "status": "COLLECTED",
            "available": True,
            "data": {
                "summary": {
                    "total": 1,
                    "running": 1,
                    "stopped": 0,
                    "healthy": 0,
                    "unhealthy": 1,
                    "restarting": 0,
                    "paused": 0,
                },
                "containers": [
                    {
                        "name": "pihole",
                        "state": "running",
                        "health": "unhealthy",
                        "restart_count": 0,
                        "exit_code": 0,
                    }
                ],
            },
        }
    }

    payload = build_discord_payload(
        report=report,
        report_title=(
            "PandaServer Operational Report"
        ),
        version="0.8.0",
    )

    description = (
        payload["embeds"][0]["description"]
    )

    assert "❌ pihole" in description
    assert (
        "• Docker container pihole is unhealthy"
        in description
    )

def test_discord_report_includes_kernel_health() -> None:
    report = build_base_report()

    report["collectors"] = {
        "kernel_health": {
            "status": "COLLECTED",
            "available": True,
            "data": {
                "total_events": 0,
                "counts": {
                    "kernel_fault": 0,
                    "hardware_error": 0,
                    "rcu_stall": 0,
                    "oom": 0,
                    "btrfs_error": 0,
                    "xfs_error": 0,
                    "io_error": 0,
                    "nvme_error": 0,
                    "disk_reset": 0,
                },
            },
        }
    }

    payload = build_discord_payload(
        report=report,
        report_title=(
            "PandaServer Operational Report"
        ),
        version="0.8.0",
    )

    description = (
        payload["embeds"][0]["description"]
    )

    assert "🧠 KERNEL HEALTH" in description
    assert "Status       : HEALTHY" in description
    assert "Events       : 0" in description
    assert "Faults       : 0" in description
    assert "Hardware     : 0" in description
    assert "OOM          : 0" in description
    assert "I/O Errors   : 0" in description
    assert "NVMe Errors  : 0" in description


def test_discord_report_shows_new_docker_restart() -> None:
    report = build_base_report()

    report["health"] = {
        "status": "WARNING",
        "score": 95,
        "issues": [
            (
                "Docker container immich_server restarted "
                "1 time(s) since the previous report"
            ),
        ],
    }

    report["collectors"] = {
        "docker": {
            "status": "COLLECTED",
            "available": True,
            "data": {
                "summary": {
                    "total": 1,
                    "running": 1,
                    "stopped": 0,
                    "healthy": 1,
                    "unhealthy": 0,
                    "restarting": 0,
                    "paused": 0,
                },
                "containers": [
                    {
                        "name": "immich_server",
                        "state": "running",
                        "health": "healthy",
                        "restart_count": 7,
                        "restart_delta": 1,
                        "exit_code": 0,
                    },
                ],
            },
        }
    }

    payload = build_discord_payload(
        report=report,
        report_title=(
            "PandaServer Operational Report"
        ),
        version="0.8.0",
    )

    description = (
        payload["embeds"][0]["description"]
    )

    assert (
        "immich_server"
        in description
    )

    assert (
        "+1 restart(s)"
        in description
    )

    assert (
        "since the previous report"
        in description
    )


def test_discord_report_hides_historical_restart_count() -> None:
    report = build_base_report()

    report["collectors"] = {
        "docker": {
            "status": "COLLECTED",
            "available": True,
            "data": {
                "summary": {
                    "total": 1,
                    "running": 1,
                    "stopped": 0,
                    "healthy": 1,
                    "unhealthy": 0,
                    "restarting": 0,
                    "paused": 0,
                },
                "containers": [
                    {
                        "name": "immich_server",
                        "state": "running",
                        "health": "healthy",
                        "restart_count": 6,
                        "restart_delta": 0,
                        "exit_code": 0,
                    },
                ],
            },
        }
    }

    payload = build_discord_payload(
        report=report,
        report_title=(
            "PandaServer Operational Report"
        ),
        version="0.8.0",
    )

    description = (
        payload["embeds"][0]["description"]
    )

    assert (
        "✅ immich_server"
        in description
    )

    assert (
        "+0 restart(s)"
        not in description
    )

    assert (
        "+6 restart(s)"
        not in description
    )