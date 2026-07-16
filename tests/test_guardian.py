from src.guardian import add_health_warnings, compare_with_previous


def build_report(
    cpu: float = 20.0,
    memory: float = 40.0,
    disk: float = 50.0,
) -> dict[str, object]:
    """Create a basic report for testing."""

    return {
        "cpu_percent": cpu,
        "memory_percent": memory,
        "disk_percent": disk,
        "internet": {
            "reachable": True,
            "error": None,
        },
        "dns": {
            "resolved": True,
            "hostname": "cloudflare.com",
            "error": None,
        },
        "warnings": [],
        "comparison": {},
    }


def test_no_warnings_when_metrics_are_healthy() -> None:
    report = build_report()

    thresholds = {
        "cpu_percent": 80,
        "memory_percent": 80,
        "disk_percent": 85,
    }

    add_health_warnings(report, thresholds)

    assert report["warnings"] == []


def test_warning_is_added_when_memory_exceeds_threshold() -> None:
    report = build_report(memory=90.0)

    thresholds = {
        "cpu_percent": 80,
        "memory_percent": 80,
        "disk_percent": 85,
    }

    add_health_warnings(report, thresholds)

    warnings = report["warnings"]

    assert len(warnings) == 1
    assert "Memory usage" in warnings[0]
    assert "90.0%" in warnings[0]


def test_network_warning_when_internet_is_unreachable() -> None:
    report = build_report()

    report["internet"] = {
        "reachable": False,
        "error": "Connection timed out",
    }

    thresholds = {
        "cpu_percent": 80,
        "memory_percent": 80,
        "disk_percent": 85,
    }

    add_health_warnings(report, thresholds)

    warnings = report["warnings"]

    assert any("Internet check failed" in warning for warning in warnings)


def test_comparison_detects_metric_changes() -> None:
    current_report = build_report(
        cpu=30.0,
        memory=45.0,
        disk=50.0,
    )

    previous_report = build_report(
        cpu=20.0,
        memory=50.0,
        disk=50.0,
    )

    compare_with_previous(current_report, previous_report)

    comparison = current_report["comparison"]

    assert comparison["cpu_percent"]["change"] == 10.0
    assert comparison["cpu_percent"]["direction"] == "increased"

    assert comparison["memory_percent"]["change"] == -5.0
    assert comparison["memory_percent"]["direction"] == "decreased"

    assert comparison["disk_percent"]["change"] == 0.0
    assert comparison["disk_percent"]["direction"] == "unchanged"


def test_comparison_handles_missing_previous_report() -> None:
    report = build_report()

    compare_with_previous(report, None)

    assert report["comparison"] == {
        "status": "No previous report available"
    }