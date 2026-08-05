from __future__ import annotations

from typing import Any


def evaluate_health(
    report: dict[str, Any],
    thresholds: dict[str, float],
) -> dict[str, Any]:
    """Evaluate report metrics and return status, score, and issues."""

    issues: list[str] = []
    score = 100

    cpu_percent = float(report.get("cpu_percent", 0.0))
    memory_percent = float(report.get("memory_percent", 0.0))
    disk_percent = float(report.get("disk_percent", 0.0))

    cpu_threshold = float(thresholds["cpu_percent"])
    memory_threshold = float(thresholds["memory_percent"])
    disk_threshold = float(thresholds["disk_percent"])

    if cpu_percent >= cpu_threshold:
        issues.append(
            f"CPU usage is above the {cpu_threshold:.0f}% threshold: "
            f"{cpu_percent:.1f}%"
        )
        score -= 10

    if memory_percent >= memory_threshold:
        issues.append(
            f"Memory usage is above the {memory_threshold:.0f}% threshold: "
            f"{memory_percent:.1f}%"
        )
        score -= 10

    if disk_percent >= disk_threshold:
        issues.append(
            f"Disk usage is above the {disk_threshold:.0f}% threshold: "
            f"{disk_percent:.1f}%"
        )
        score -= 15

    internet = report.get("internet", {})
    dns = report.get("dns", {})

    if not bool(internet.get("reachable", False)):
        issues.append(
            "Internet check failed: "
            f"{internet.get('error') or 'unknown error'}"
        )
        score -= 20

    if not bool(dns.get("resolved", False)):
        issues.append(
            "DNS resolution failed for "
            f"{dns.get('hostname', 'unknown hostname')}: "
            f"{dns.get('error') or 'unknown error'}"
        )
        score -= 20

    docker = report.get("docker")

    if isinstance(docker, dict):
        if not bool(docker.get("service_running", True)):
            issues.append("Docker service is not running")
            score -= 30

        unhealthy_count = int(
            docker.get("unhealthy_count", 0)
        )
        stopped_count = int(
            docker.get("stopped_count", 0)
        )

        if unhealthy_count > 0:
            issues.append(
                f"{unhealthy_count} unhealthy Docker container(s)"
            )
            score -= unhealthy_count * 10

        if stopped_count > 0:
            issues.append(
                f"{stopped_count} stopped Docker container(s)"
            )
            score -= stopped_count * 5

    storage = report.get("storage")

    if isinstance(storage, dict):
        array_state = str(
            storage.get("array_state", "STARTED")
        )
        missing_disks = int(
            storage.get("missing_disks", 0)
        )
        problem_disks = int(
            storage.get("problem_disks", 0)
        )
        array_percent = float(
            storage.get("array_percent", 0.0)
        )
        cache_percent = float(
            storage.get("cache_percent", 0.0)
        )

        if array_state != "STARTED":
            issues.append(f"Array state is {array_state}")
            score -= 35

        if missing_disks > 0:
            issues.append(
                f"{missing_disks} missing array disk(s)"
            )
            score -= missing_disks * 25

        if problem_disks > 0:
            issues.append(
                f"{problem_disks} problem array disk(s)"
            )
            score -= problem_disks * 25

        if array_percent >= 95:
            issues.append(
                f"Array usage is {array_percent:.0f}%"
            )
            score -= 20
        elif array_percent >= 90:
            issues.append(
                f"Array usage is {array_percent:.0f}%"
            )
            score -= 15
        elif array_percent >= 80:
            issues.append(
                f"Array usage is {array_percent:.0f}%"
            )
            score -= 5

        if cache_percent >= 95:
            issues.append(
                f"Cache usage is {cache_percent:.0f}%"
            )
            score -= 20
        elif cache_percent >= 90:
            issues.append(
                f"Cache usage is {cache_percent:.0f}%"
            )
            score -= 15
        elif cache_percent >= 80:
            issues.append(
                f"Cache usage is {cache_percent:.0f}%"
            )
            score -= 5

    score = max(score, 0)

    if score < 60:
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
