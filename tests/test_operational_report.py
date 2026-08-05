from homelab_guardian.reports.operational import (
    build_operational_report,
)


def test_build_healthy_operational_report() -> None:
    report = {
        "timestamp": "2026-08-05T14:30:00-04:00",
        "hostname": "PandaServer",
        "cpu_percent": 5.0,
        "memory_percent": 5.0,
        "cpu_temperature": 32.6,
        "load_average": 0.03,
        "uptime": "6 days, 13 minutes",
        "storage": {
            "array_percent": 2,
            "cache_percent": 3,
        },
        "docker": {
            "running_count": 2,
            "stopped_count": 0,
            "unhealthy_count": 0,
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

    output = build_operational_report(
        report=report,
        report_title="PandaServer Operational Report",
        version="0.7.0",
    )

    assert "🐼 PandaServer Operational Report" in output
    assert "🟢 OVERALL HEALTH" in output
    assert "Health Score : 100 / 100" in output
    assert "CPU Temp     : 32.6°C" in output
    assert "Array Usage  : 2%" in output
    assert "Running      : 2" in output
    assert "✅ Everything looks healthy." in output


def test_missing_future_collectors_are_not_healthy() -> None:
    report = {
        "timestamp": "2026-08-05T14:30:00-04:00",
        "cpu_percent": 10,
        "memory_percent": 20,
        "health": {
            "status": "HEALTHY",
            "score": 100,
            "issues": [],
        },
    }

    output = build_operational_report(
        report=report,
        report_title="PandaServer Operational Report",
        version="0.7.0",
    )

    assert "CPU Temp     : Unavailable" in output
    assert "Array Usage  : Not collected" in output
    assert "Running      : Not collected" in output
    assert "UPTIME\nUnavailable" in output