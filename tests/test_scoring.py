from homelab_guardian.scoring import evaluate_health


THRESHOLDS = {
    "cpu_percent": 80,
    "memory_percent": 80,
    "disk_percent": 85,
}


def test_healthy_report_scores_100() -> None:
    report = {
        "cpu_percent": 20,
        "memory_percent": 30,
        "disk_percent": 40,
        "internet": {
            "reachable": True,
            "error": None,
        },
        "dns": {
            "resolved": True,
            "hostname": "cloudflare.com",
            "error": None,
        },
    }

    result = evaluate_health(report, THRESHOLDS)

    assert result["status"] == "HEALTHY"
    assert result["score"] == 100
    assert result["issues"] == []
    assert (
        result["issue_summary"]
        == "No monitored issues detected."
    )


def test_warning_report_deducts_points() -> None:
    report = {
        "cpu_percent": 90,
        "memory_percent": 30,
        "disk_percent": 40,
        "internet": {
            "reachable": True,
            "error": None,
        },
        "dns": {
            "resolved": True,
            "hostname": "cloudflare.com",
            "error": None,
        },
    }

    result = evaluate_health(report, THRESHOLDS)

    assert result["status"] == "WARNING"
    assert result["score"] == 90
    assert len(result["issues"]) == 1


def test_critical_report_never_scores_below_zero() -> None:
    report = {
        "cpu_percent": 95,
        "memory_percent": 95,
        "disk_percent": 99,
        "internet": {
            "reachable": False,
            "error": "timeout",
        },
        "dns": {
            "resolved": False,
            "hostname": "cloudflare.com",
            "error": "resolution failed",
        },
        "docker": {
            "service_running": False,
            "unhealthy_count": 3,
            "stopped_count": 4,
        },
        "storage": {
            "array_state": "STOPPED",
            "missing_disks": 1,
            "problem_disks": 1,
            "array_percent": 99,
            "cache_percent": 99,
        },
    }

    result = evaluate_health(report, THRESHOLDS)

    assert result["status"] == "CRITICAL"
    assert result["score"] == 0
    assert len(result["issues"]) > 5

def test_smart_healthy_does_not_reduce_score() -> None:
    report = {
        "cpu_percent": 20,
        "memory_percent": 30,
        "disk_percent": 40,
        "internet": {
            "reachable": True,
            "error": None,
        },
        "dns": {
            "resolved": True,
            "hostname": "cloudflare.com",
            "error": None,
        },
        "collectors": {
            "smart": {
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "parity": {
                        "available": True,
                        "smart": {
                            "passed": True,
                            "reallocated_sectors": 0,
                            "pending_sectors": 0,
                            "uncorrectable_sectors": 0,
                            "media_errors": None,
                            "critical_warning": None,
                        },
                    }
                },
            }
        },
    }

    result = evaluate_health(
        report,
        THRESHOLDS,
    )

    assert result["status"] == "HEALTHY"
    assert result["score"] == 100
    assert result["issues"] == []


def test_reallocated_sector_creates_warning() -> None:
    report = {
        "cpu_percent": 20,
        "memory_percent": 30,
        "disk_percent": 40,
        "internet": {
            "reachable": True,
            "error": None,
        },
        "dns": {
            "resolved": True,
            "hostname": "cloudflare.com",
            "error": None,
        },
        "collectors": {
            "smart": {
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "disk1": {
                        "available": True,
                        "smart": {
                            "passed": True,
                            "reallocated_sectors": 2,
                            "pending_sectors": 0,
                            "uncorrectable_sectors": 0,
                            "media_errors": None,
                            "critical_warning": None,
                        },
                    }
                },
            }
        },
    }

    result = evaluate_health(
        report,
        THRESHOLDS,
    )

    assert result["status"] == "WARNING"
    assert result["score"] == 90
    assert any(
        "reallocated" in issue.lower()
        for issue in result["issues"]
    )


def test_pending_sector_forces_critical() -> None:
    report = {
        "cpu_percent": 20,
        "memory_percent": 30,
        "disk_percent": 40,
        "internet": {
            "reachable": True,
            "error": None,
        },
        "dns": {
            "resolved": True,
            "hostname": "cloudflare.com",
            "error": None,
        },
        "collectors": {
            "smart": {
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "disk1": {
                        "available": True,
                        "smart": {
                            "passed": True,
                            "reallocated_sectors": 0,
                            "pending_sectors": 1,
                            "uncorrectable_sectors": 0,
                            "media_errors": None,
                            "critical_warning": None,
                        },
                    }
                },
            }
        },
    }

    result = evaluate_health(
        report,
        THRESHOLDS,
    )

    assert result["status"] == "CRITICAL"
    assert result["score"] == 65
    assert any(
        "pending" in issue.lower()
        for issue in result["issues"]
    )


def test_nvme_media_error_forces_critical() -> None:
    report = {
        "cpu_percent": 20,
        "memory_percent": 30,
        "disk_percent": 40,
        "internet": {
            "reachable": True,
            "error": None,
        },
        "dns": {
            "resolved": True,
            "hostname": "cloudflare.com",
            "error": None,
        },
        "collectors": {
            "smart": {
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "cache": {
                        "available": True,
                        "smart": {
                            "passed": True,
                            "reallocated_sectors": None,
                            "pending_sectors": None,
                            "uncorrectable_sectors": None,
                            "media_errors": 1,
                            "critical_warning": 0,
                        },
                    }
                },
            }
        },
    }

    result = evaluate_health(
        report,
        THRESHOLDS,
    )

    assert result["status"] == "CRITICAL"
    assert result["score"] == 65
    assert any(
        "media error" in issue.lower()
        for issue in result["issues"]
    )


def test_smart_failure_forces_critical() -> None:
    report = {
        "cpu_percent": 20,
        "memory_percent": 30,
        "disk_percent": 40,
        "internet": {
            "reachable": True,
            "error": None,
        },
        "dns": {
            "resolved": True,
            "hostname": "cloudflare.com",
            "error": None,
        },
        "collectors": {
            "smart": {
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "parity": {
                        "available": True,
                        "smart": {
                            "passed": False,
                            "reallocated_sectors": 0,
                            "pending_sectors": 0,
                            "uncorrectable_sectors": 0,
                            "media_errors": None,
                            "critical_warning": None,
                        },
                    }
                },
            }
        },
    }

    result = evaluate_health(
        report,
        THRESHOLDS,
    )

    assert result["status"] == "CRITICAL"
    assert result["score"] == 50
    assert any(
        "smart overall health failure"
        in issue.lower()
        for issue in result["issues"]
    )