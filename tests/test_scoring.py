from homelab_guardian.scoring import (
    evaluate_health,
    evaluate_kernel_health,
)

THRESHOLDS = {
    "cpu_percent": 80,
    "memory_percent": 80,
    "disk_percent": 85,
    "hdd_temperature_warning": 45,
    "hdd_temperature_critical": 55,
    "nvme_temperature_warning": 70,
    "nvme_temperature_critical": 80,
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

    result = evaluate_health(
        report,
        THRESHOLDS,
    )

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

    result = evaluate_health(
        report,
        THRESHOLDS,
    )

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
        "storage": {
            "array_state": "STOPPED",
            "missing_disks": 1,
            "problem_disks": 1,
            "array_percent": 99,
            "cache_percent": 99,
        },
        "collectors": {
            "docker": {
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "containers": [
                        {
                            "name": "broken-container",
                            "state": "restarting",
                            "health": "unhealthy",
                            "restart_count": 10,
                            "exit_code": 1,
                        },
                        {
                            "name": "failed-container",
                            "state": "exited",
                            "health": None,
                            "restart_count": 5,
                            "exit_code": 137,
                        },
                    ]
                },
            }
        },
    }

    result = evaluate_health(
        report,
        THRESHOLDS,
    )

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


def test_hdd_temperature_warning() -> None:
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
                            "protocol": "ATA",
                            "passed": True,
                            "temperature_celsius": 47,
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

    assert result["status"] == "WARNING"
    assert result["score"] == 90
    assert any(
        "temperature is elevated"
        in issue.lower()
        for issue in result["issues"]
    )


def test_hdd_temperature_critical() -> None:
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
                            "protocol": "ATA",
                            "passed": True,
                            "temperature_celsius": 56,
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
    assert result["score"] == 80
    assert any(
        "temperature is critical"
        in issue.lower()
        for issue in result["issues"]
    )


def test_nvme_uses_higher_temperature_threshold() -> None:
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
                            "protocol": "NVMe",
                            "passed": True,
                            "temperature_celsius": 60,
                            "reallocated_sectors": None,
                            "pending_sectors": None,
                            "uncorrectable_sectors": None,
                            "media_errors": 0,
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

    assert result["status"] == "HEALTHY"
    assert result["score"] == 100
    assert result["issues"] == []


def test_unhealthy_docker_container_creates_warning() -> None:
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
            "docker": {
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "containers": [
                        {
                            "name": "pihole",
                            "state": "running",
                            "health": "unhealthy",
                            "restart_count": 0,
                            "exit_code": 0,
                        }
                    ]
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
        "unhealthy" in issue.lower()
        for issue in result["issues"]
    )


def test_restarting_docker_container_creates_warning() -> None:
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
            "docker": {
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "containers": [
                        {
                            "name": "UptimeKuma",
                            "state": "restarting",
                            "health": None,
                            "restart_count": 2,
                            "exit_code": 1,
                        }
                    ]
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
        "restarting" in issue.lower()
        for issue in result["issues"]
    )


def test_docker_restart_count_alone_does_not_warn() -> None:
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
            "docker": {
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "containers": [
                        {
                            "name": "pihole",
                            "state": "running",
                            "health": "healthy",
                            "restart_count": 6,
                            "restart_delta": 0,
                            "exit_code": 0,
                        }
                    ]
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


def test_nonzero_docker_exit_code_creates_warning() -> None:
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
            "docker": {
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "containers": [
                        {
                            "name": "paperless",
                            "state": "exited",
                            "health": None,
                            "restart_count": 0,
                            "exit_code": 137,
                        }
                    ]
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
        "exited with code 137"
        in issue.lower()
        for issue in result["issues"]
    )

def test_kernel_health_clean() -> None:
    collector = {
        "status": "COLLECTED",
        "data": {
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
            }
        },
    }

    result = evaluate_kernel_health(
        collector
    )

    assert result["issues"] == []
    assert result["score_deduction"] == 0
    assert result["critical"] is False


def test_kernel_fault_is_critical() -> None:
    collector = {
        "status": "COLLECTED",
        "data": {
            "counts": {
                "kernel_fault": 1,
            }
        },
    }

    result = evaluate_kernel_health(
        collector
    )

    assert result["critical"] is True
    assert result["score_deduction"] == 40
    assert (
        "fault/oops/panic"
        in result["issues"][0]
    )


def test_hardware_error_is_critical() -> None:
    collector = {
        "status": "COLLECTED",
        "data": {
            "counts": {
                "hardware_error": 1,
            }
        },
    }

    result = evaluate_kernel_health(
        collector
    )

    assert result["critical"] is True
    assert result["score_deduction"] == 40


def test_single_oom_event_is_warning() -> None:
    collector = {
        "status": "COLLECTED",
        "data": {
            "counts": {
                "oom": 1,
            }
        },
    }

    result = evaluate_kernel_health(
        collector
    )

    assert result["critical"] is False
    assert result["score_deduction"] == 10
    assert len(result["issues"]) == 1


def test_multiple_oom_events_become_critical() -> None:
    collector = {
        "status": "COLLECTED",
        "data": {
            "counts": {
                "oom": 3,
            }
        },
    }

    result = evaluate_kernel_health(
        collector
    )

    assert result["critical"] is True
    assert result["score_deduction"] == 30

def test_historical_docker_restart_count_does_not_warn() -> None:
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
            "docker": {
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "containers": [
                        {
                            "name": "immich_server",
                            "state": "running",
                            "health": "healthy",
                            "restart_count": 6,
                            "restart_delta": 0,
                            "exit_code": 0,
                        }
                    ]
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


def test_new_docker_restart_creates_warning() -> None:
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
            "docker": {
                "status": "COLLECTED",
                "available": True,
                "data": {
                    "containers": [
                        {
                            "name": "immich_server",
                            "state": "running",
                            "health": "healthy",
                            "restart_count": 7,
                            "restart_delta": 1,
                            "exit_code": 0,
                        }
                    ]
                },
            }
        },
    }

    result = evaluate_health(
        report,
        THRESHOLDS,
    )

    assert result["status"] == "WARNING"
    assert result["score"] == 95

    assert any(
        "since the previous report"
        in issue.lower()
        for issue in result["issues"]
    )