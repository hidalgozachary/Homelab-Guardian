from __future__ import annotations

from typing import Any


def evaluate_smart_health(
    smart_collector: dict[str, Any],
    thresholds: dict[str, float],
) -> dict[str, Any]:
    """Evaluate normalized SMART collector data."""

    issues: list[str] = []
    score_deduction = 0
    critical = False

    if not isinstance(smart_collector, dict):
        return {
            "issues": issues,
            "score_deduction": score_deduction,
            "critical": critical,
        }

    if smart_collector.get("status") != "COLLECTED":
        return {
            "issues": issues,
            "score_deduction": score_deduction,
            "critical": critical,
        }

    devices = smart_collector.get("data", {})

    if not isinstance(devices, dict):
        return {
            "issues": issues,
            "score_deduction": score_deduction,
            "critical": critical,
        }

    for device_name, device_result in devices.items():
        if not isinstance(device_result, dict):
            continue

        if not device_result.get("available", False):
            continue

        smart = device_result.get("smart")

        if not isinstance(smart, dict):
            continue

        label = device_name.replace("_", " ").title()

        protocol = smart.get("protocol")
        temperature = smart.get(
            "temperature_celsius"
        )

        if isinstance(temperature, int):
            if protocol == "NVMe":
                warning_temperature = float(
                    thresholds[
                        "nvme_temperature_warning"
                    ]
                )
                critical_temperature = float(
                    thresholds[
                        "nvme_temperature_critical"
                    ]
                )
            else:
                warning_temperature = float(
                    thresholds[
                        "hdd_temperature_warning"
                    ]
                )
                critical_temperature = float(
                    thresholds[
                        "hdd_temperature_critical"
                    ]
                )

            if temperature >= critical_temperature:
                issues.append(
                    f"{label} temperature is critical "
                    f"at {temperature}°C"
                )
                score_deduction += 20
                critical = True

            elif temperature >= warning_temperature:
                issues.append(
                    f"{label} temperature is elevated "
                    f"at {temperature}°C"
                )
                score_deduction += 10

        passed = smart.get("passed")

        if passed is False:
            issues.append(
                f"{label} reports SMART overall health failure"
            )
            score_deduction += 50
            critical = True

        reallocated = smart.get(
            "reallocated_sectors"
        )

        if (
            isinstance(reallocated, int)
            and reallocated > 0
        ):
            issues.append(
                f"{label} has {reallocated} reallocated sector(s)"
            )
            score_deduction += 10

        pending = smart.get(
            "pending_sectors"
        )

        if (
            isinstance(pending, int)
            and pending > 0
        ):
            issues.append(
                f"{label} has {pending} pending sector(s)"
            )
            score_deduction += 35
            critical = True

        uncorrectable = smart.get(
            "uncorrectable_sectors"
        )

        if (
            isinstance(uncorrectable, int)
            and uncorrectable > 0
        ):
            issues.append(
                f"{label} has "
                f"{uncorrectable} offline uncorrectable sector(s)"
            )
            score_deduction += 40
            critical = True

        media_errors = smart.get(
            "media_errors"
        )

        if (
            isinstance(media_errors, int)
            and media_errors > 0
        ):
            issues.append(
                f"{label} reports "
                f"{media_errors} NVMe media error(s)"
            )
            score_deduction += 35
            critical = True

        critical_warning = smart.get(
            "critical_warning"
        )

        if (
            isinstance(critical_warning, int)
            and critical_warning > 0
        ):
            issues.append(
                f"{label} reports an NVMe critical warning"
            )
            score_deduction += 40
            critical = True

    return {
        "issues": issues,
        "score_deduction": score_deduction,
        "critical": critical,
    }


def evaluate_kernel_health(
    kernel_collector: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate normalized kernel-health collector data."""

    issues: list[str] = []
    score_deduction = 0
    critical = False

    if not isinstance(kernel_collector, dict):
        return {
            "issues": issues,
            "score_deduction": score_deduction,
            "critical": critical,
        }

    if kernel_collector.get("status") != "COLLECTED":
        return {
            "issues": issues,
            "score_deduction": score_deduction,
            "critical": critical,
        }

    data = kernel_collector.get(
        "data",
        {},
    )

    if not isinstance(data, dict):
        return {
            "issues": issues,
            "score_deduction": score_deduction,
            "critical": critical,
        }

    counts = data.get(
        "counts",
        {},
    )

    if not isinstance(counts, dict):
        return {
            "issues": issues,
            "score_deduction": score_deduction,
            "critical": critical,
        }

    kernel_faults = int(
        counts.get("kernel_fault", 0)
    )

    hardware_errors = int(
        counts.get("hardware_error", 0)
    )

    rcu_stalls = int(
        counts.get("rcu_stall", 0)
    )

    oom_events = int(
        counts.get("oom", 0)
    )

    btrfs_errors = int(
        counts.get("btrfs_error", 0)
    )

    xfs_errors = int(
        counts.get("xfs_error", 0)
    )

    io_errors = int(
        counts.get("io_error", 0)
    )

    nvme_errors = int(
        counts.get("nvme_error", 0)
    )

    disk_resets = int(
        counts.get("disk_reset", 0)
    )

    if kernel_faults > 0:
        issues.append(
            f"Kernel reports {kernel_faults} "
            "fault/oops/panic event(s)"
        )
        score_deduction += 40
        critical = True

    if hardware_errors > 0:
        issues.append(
            f"Kernel reports {hardware_errors} "
            "hardware/MCE/EDAC error event(s)"
        )
        score_deduction += 40
        critical = True

    if btrfs_errors > 0:
        issues.append(
            f"Kernel reports {btrfs_errors} "
            "BTRFS error event(s)"
        )
        score_deduction += 35
        critical = True

    if xfs_errors > 0:
        issues.append(
            f"Kernel reports {xfs_errors} "
            "XFS error event(s)"
        )
        score_deduction += 35
        critical = True

    if rcu_stalls > 0:
        issues.append(
            f"Kernel reports {rcu_stalls} "
            "RCU stall event(s)"
        )
        score_deduction += min(
            5 * rcu_stalls,
            20,
        )

    if oom_events > 0:
        issues.append(
            f"Kernel reports {oom_events} "
            "out-of-memory event(s)"
        )
        score_deduction += min(
            10 * oom_events,
            30,
        )

        if oom_events >= 3:
            critical = True

    if io_errors > 0:
        issues.append(
            f"Kernel reports {io_errors} "
            "I/O error event(s)"
        )
        score_deduction += min(
            10 * io_errors,
            30,
        )

        if io_errors >= 3:
            critical = True

    if nvme_errors > 0:
        issues.append(
            f"Kernel reports {nvme_errors} "
            "NVMe error/timeout/reset event(s)"
        )
        score_deduction += min(
            10 * nvme_errors,
            30,
        )

        if nvme_errors >= 3:
            critical = True

    if disk_resets > 0:
        issues.append(
            f"Kernel reports {disk_resets} "
            "disk/controller reset event(s)"
        )
        score_deduction += min(
            5 * disk_resets,
            20,
        )

    return {
        "issues": issues,
        "score_deduction": score_deduction,
        "critical": critical,
    }


def evaluate_docker_health(
    docker_collector: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate normalized Docker collector data."""

    issues: list[str] = []
    score_deduction = 0
    critical = False

    if not isinstance(docker_collector, dict):
        return {
            "issues": issues,
            "score_deduction": score_deduction,
            "critical": critical,
        }

    if docker_collector.get("status") != "COLLECTED":
        return {
            "issues": issues,
            "score_deduction": score_deduction,
            "critical": critical,
        }

    data = docker_collector.get(
        "data",
        {},
    )

    if not isinstance(data, dict):
        return {
            "issues": issues,
            "score_deduction": score_deduction,
            "critical": critical,
        }

    containers = data.get(
        "containers",
        [],
    )

    if not isinstance(containers, list):
        return {
            "issues": issues,
            "score_deduction": score_deduction,
            "critical": critical,
        }

    for container in containers:
        if not isinstance(container, dict):
            continue

        name = str(
            container.get("name")
            or "Unnamed container"
        )

        state = container.get("state")
        health = container.get("health")

        restart_count = container.get(
            "restart_count"
        )

        exit_code = container.get(
            "exit_code"
        )

        if health == "unhealthy":
            issues.append(
                f"Docker container {name} is unhealthy"
            )
            score_deduction += 10

        if state == "restarting":
            issues.append(
                f"Docker container {name} is restarting"
            )
            score_deduction += 10

        if (
            isinstance(restart_count, int)
            and restart_count >= 5
        ):
            issues.append(
                f"Docker container {name} has restarted "
                f"{restart_count} times"
            )
            score_deduction += 5

        if (
            state == "exited"
            and isinstance(exit_code, int)
            and exit_code != 0
        ):
            issues.append(
                f"Docker container {name} exited "
                f"with code {exit_code}"
            )
            score_deduction += 10

    return {
        "issues": issues,
        "score_deduction": score_deduction,
        "critical": critical,
    }


def evaluate_health(
    report: dict[str, Any],
    thresholds: dict[str, float],
) -> dict[str, Any]:
    """Evaluate report metrics and return status, score, and issues."""

    issues: list[str] = []
    score = 100

    cpu_percent = float(
        report.get("cpu_percent", 0.0)
    )

    memory_percent = float(
        report.get("memory_percent", 0.0)
    )

    disk_percent = float(
        report.get("disk_percent", 0.0)
    )

    cpu_threshold = float(
        thresholds["cpu_percent"]
    )

    memory_threshold = float(
        thresholds["memory_percent"]
    )

    disk_threshold = float(
        thresholds["disk_percent"]
    )

    if cpu_percent >= cpu_threshold:
        issues.append(
            f"CPU usage is above the "
            f"{cpu_threshold:.0f}% threshold: "
            f"{cpu_percent:.1f}%"
        )
        score -= 10

    if memory_percent >= memory_threshold:
        issues.append(
            f"Memory usage is above the "
            f"{memory_threshold:.0f}% threshold: "
            f"{memory_percent:.1f}%"
        )
        score -= 10

    if disk_percent >= disk_threshold:
        issues.append(
            f"Disk usage is above the "
            f"{disk_threshold:.0f}% threshold: "
            f"{disk_percent:.1f}%"
        )
        score -= 15

    internet = report.get(
        "internet",
        {},
    )

    dns = report.get(
        "dns",
        {},
    )

    if not bool(
        internet.get(
            "reachable",
            False,
        )
    ):
        issues.append(
            "Internet check failed: "
            f"{internet.get('error') or 'unknown error'}"
        )
        score -= 20

    if not bool(
        dns.get(
            "resolved",
            False,
        )
    ):
        issues.append(
            "DNS resolution failed for "
            f"{dns.get('hostname', 'unknown hostname')}: "
            f"{dns.get('error') or 'unknown error'}"
        )
        score -= 20

    storage = report.get(
        "storage"
    )

    if isinstance(storage, dict):
        array_state = str(
            storage.get(
                "array_state",
                "STARTED",
            )
        )

        missing_disks = int(
            storage.get(
                "missing_disks",
                0,
            )
        )

        problem_disks = int(
            storage.get(
                "problem_disks",
                0,
            )
        )

        array_percent = float(
            storage.get(
                "array_percent",
                0.0,
            )
        )

        cache_percent = float(
            storage.get(
                "cache_percent",
                0.0,
            )
        )

        if array_state != "STARTED":
            issues.append(
                f"Array state is {array_state}"
            )
            score -= 35

        if missing_disks > 0:
            issues.append(
                f"{missing_disks} "
                "missing array disk(s)"
            )
            score -= missing_disks * 25

        if problem_disks > 0:
            issues.append(
                f"{problem_disks} "
                "problem array disk(s)"
            )
            score -= problem_disks * 25

        if array_percent >= 95:
            issues.append(
                f"Array usage is "
                f"{array_percent:.0f}%"
            )
            score -= 20

        elif array_percent >= 90:
            issues.append(
                f"Array usage is "
                f"{array_percent:.0f}%"
            )
            score -= 15

        elif array_percent >= 80:
            issues.append(
                f"Array usage is "
                f"{array_percent:.0f}%"
            )
            score -= 5

        if cache_percent >= 95:
            issues.append(
                f"Cache usage is "
                f"{cache_percent:.0f}%"
            )
            score -= 20

        elif cache_percent >= 90:
            issues.append(
                f"Cache usage is "
                f"{cache_percent:.0f}%"
            )
            score -= 15

        elif cache_percent >= 80:
            issues.append(
                f"Cache usage is "
                f"{cache_percent:.0f}%"
            )
            score -= 5

    collectors = report.get(
        "collectors",
        {},
    )

    smart_result = {
        "issues": [],
        "score_deduction": 0,
        "critical": False,
    }

    kernel_result = {
        "issues": [],
        "score_deduction": 0,
        "critical": False,
    }

    docker_result = {
        "issues": [],
        "score_deduction": 0,
        "critical": False,
    }

    if isinstance(
        collectors,
        dict,
    ):
        smart_result = evaluate_smart_health(
            collectors.get(
                "smart",
                {},
            ),
            thresholds,
        )

        kernel_result = evaluate_kernel_health(
            collectors.get(
                "kernel_health",
                {},
            )
        )

        docker_result = evaluate_docker_health(
            collectors.get(
                "docker",
                {},
            )
        )

    issues.extend(
        smart_result["issues"]
    )

    issues.extend(
        kernel_result["issues"]
    )

    issues.extend(
        docker_result["issues"]
    )

    score -= int(
        smart_result["score_deduction"]
    )

    score -= int(
        kernel_result["score_deduction"]
    )

    score -= int(
        docker_result["score_deduction"]
    )

    smart_critical = bool(
        smart_result["critical"]
    )

    kernel_critical = bool(
        kernel_result["critical"]
    )

    docker_critical = bool(
        docker_result["critical"]
    )

    score = max(
        score,
        0,
    )

    if (
        smart_critical
        or kernel_critical
        or docker_critical
        or score < 60
    ):
        status = "CRITICAL"

    elif issues:
        status = "WARNING"

    else:
        status = "HEALTHY"

    issue_summary = (
        "; ".join(issues)
        if issues
        else "No monitored issues detected."
    )

    return {
        "status": status,
        "score": score,
        "issues": issues,
        "issue_summary": issue_summary,
    }