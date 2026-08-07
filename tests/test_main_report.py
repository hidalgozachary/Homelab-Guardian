from homelab_guardian import main


def test_build_report_includes_collectors(
    monkeypatch,
) -> None:
    settings = {
        "network": {
            "internet_url": "https://example.com",
            "timeout_seconds": 5,
            "dns_hostname": "example.com",
        },
        "warning_thresholds": {
            "cpu_percent": 80,
            "memory_percent": 80,
            "disk_percent": 85,
        },
    }

    monkeypatch.setattr(
        main,
        "collect_system_metrics",
        lambda _settings: {
            "cpu_percent": 10,
            "memory_percent": 20,
            "disk_percent": 30,
        },
    )

    monkeypatch.setattr(
        main,
        "check_internet",
        lambda _url, _timeout: {
            "reachable": True,
            "status_code": 200,
            "response_time_ms": 10,
            "error": None,
        },
    )

    monkeypatch.setattr(
        main,
        "check_dns",
        lambda _hostname: {
            "resolved": True,
            "hostname": "example.com",
            "ip_address": "203.0.113.10",
            "error": None,
        },
    )

    monkeypatch.setattr(
        main,
        "run_collectors",
        lambda _collectors: {
            "unraid": {
                "name": "unraid",
                "status": "UNAVAILABLE",
                "available": False,
                "data": {
                    "collector_status": "NOT_UNRAID",
                },
                "error": None,
            }
        },
    )

    report = main.build_report(settings)

    assert "collectors" in report
    assert report["collectors"]["unraid"]["status"] == "UNAVAILABLE"
    assert report["health"]["status"] == "HEALTHY"


def test_build_report_adds_health_after_collection(
    monkeypatch,
) -> None:
    settings = {
        "network": {
            "internet_url": "https://example.com",
            "timeout_seconds": 5,
            "dns_hostname": "example.com",
        },
        "warning_thresholds": {
            "cpu_percent": 80,
            "memory_percent": 80,
            "disk_percent": 85,
        },
    }

    monkeypatch.setattr(
        main,
        "collect_system_metrics",
        lambda _settings: {
            "cpu_percent": 95,
            "memory_percent": 20,
            "disk_percent": 30,
        },
    )

    monkeypatch.setattr(
        main,
        "check_internet",
        lambda _url, _timeout: {
            "reachable": True,
            "status_code": 200,
            "response_time_ms": 10,
            "error": None,
        },
    )

    monkeypatch.setattr(
        main,
        "check_dns",
        lambda _hostname: {
            "resolved": True,
            "hostname": "example.com",
            "ip_address": "203.0.113.10",
            "error": None,
        },
    )

    monkeypatch.setattr(
        main,
        "run_collectors",
        lambda _collectors: {},
    )

    report = main.build_report(settings)

    assert report["health"]["status"] == "WARNING"
    assert report["health"]["score"] == 90

def test_build_report_passes_unraid_assignments_to_smart(
    monkeypatch,
) -> None:
    settings = {
        "network": {
            "internet_url": "https://example.com",
            "timeout_seconds": 5,
            "dns_hostname": "example.com",
        },
        "warning_thresholds": {
            "cpu_percent": 80,
            "memory_percent": 80,
            "disk_percent": 85,
        },
    }

    monkeypatch.setattr(
        main,
        "collect_system_metrics",
        lambda _settings: {
            "cpu_percent": 10,
            "memory_percent": 20,
            "disk_percent": 30,
        },
    )

    monkeypatch.setattr(
        main,
        "check_internet",
        lambda _url, _timeout: {
            "reachable": True,
            "status_code": 200,
            "response_time_ms": 10,
            "error": None,
        },
    )

    monkeypatch.setattr(
        main,
        "check_dns",
        lambda _hostname: {
            "resolved": True,
            "hostname": "example.com",
            "ip_address": "203.0.113.10",
            "error": None,
        },
    )

    assignments = {
        "parity": {
            "assigned": True,
            "role": "parity",
            "device": "sdb",
        },
        "disk1": {
            "assigned": True,
            "role": "array_disk",
            "device": "sdc",
        },
    }

    collector_calls = []

    def fake_run_collectors(collectors):
        collector_calls.append(collectors)

        if len(collector_calls) == 1:
            return {
                "host": {
                    "name": "host",
                    "status": "COLLECTED",
                    "available": True,
                    "data": {},
                    "error": None,
                },
                "unraid": {
                    "name": "unraid",
                    "status": "COLLECTED",
                    "available": True,
                    "data": {
                        "disk_assignments": assignments,
                    },
                    "error": None,
                },
                "storage": {
                    "name": "storage",
                    "status": "COLLECTED",
                    "available": True,
                    "data": {},
                    "error": None,
                },
            }

        return {
            "smart": {
                "name": "smart",
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "parity": {
                        "available": True,
                    }
                },
                "error": None,
            }
        }

    monkeypatch.setattr(
        main,
        "run_collectors",
        fake_run_collectors,
    )

    report = main.build_report(settings)

    assert len(collector_calls) == 2

    smart_collector = collector_calls[1][0]

    assert isinstance(
        smart_collector,
        main.SmartCollector,
    )

    assert smart_collector.assignments == assignments

    assert "smart" in report["collectors"]
    assert (
        report["collectors"]["smart"]["status"]
        == "COLLECTED"
    )