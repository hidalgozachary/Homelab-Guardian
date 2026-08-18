from __future__ import annotations

import json
import subprocess
from typing import Any

from homelab_guardian.models import CollectorResult


DOCKER_COMMAND = "docker"


def run_docker_ps() -> dict[str, Any]:
    """Run a read-only Docker container inventory command."""

    command = [
        DOCKER_COMMAND,
        "ps",
        "-a",
        "--format",
        "{{json .}}",
    ]

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        return {
            "available": False,
            "containers": [],
            "error": "docker command is not available",
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "containers": [],
            "error": "docker ps command timed out",
        }
    except OSError as error:
        return {
            "available": False,
            "containers": [],
            "error": str(error),
        }

    if completed.returncode != 0:
        error_message = (
            completed.stderr.strip()
            or (
                "docker ps exited with status "
                f"{completed.returncode}"
            )
        )

        return {
            "available": False,
            "containers": [],
            "error": error_message,
        }

    containers: list[dict[str, Any]] = []

    for raw_line in completed.stdout.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue

        if isinstance(payload, dict):
            containers.append(payload)

    return {
        "available": True,
        "containers": containers,
        "error": None,
    }


def inspect_container(
    container_name: str,
) -> dict[str, Any]:
    """Return read-only Docker inspection data for one container."""

    command = [
        DOCKER_COMMAND,
        "inspect",
        "--format",
        "{{json .}}",
        container_name,
    ]

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        return {
            "available": False,
            "payload": None,
            "error": "docker command is not available",
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "payload": None,
            "error": (
                "docker inspect timed out for "
                f"{container_name}"
            ),
        }
    except OSError as error:
        return {
            "available": False,
            "payload": None,
            "error": str(error),
        }

    if completed.returncode != 0:
        error_message = (
            completed.stderr.strip()
            or (
                "docker inspect failed for "
                f"{container_name}"
            )
        )

        return {
            "available": False,
            "payload": None,
            "error": error_message,
        }

    stdout = completed.stdout.strip()

    if not stdout:
        return {
            "available": False,
            "payload": None,
            "error": (
                "docker inspect produced no output for "
                f"{container_name}"
            ),
        }

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return {
            "available": False,
            "payload": None,
            "error": (
                "docker inspect returned invalid JSON for "
                f"{container_name}"
            ),
        }

    if not isinstance(payload, dict):
        return {
            "available": False,
            "payload": None,
            "error": (
                "docker inspect returned an unexpected "
                f"payload for {container_name}"
            ),
        }

    return {
        "available": True,
        "payload": payload,
        "error": None,
    }


def normalize_health(
    status: str,
) -> str | None:
    """Extract Docker health information from ps status text."""

    normalized = status.lower()

    if "(healthy)" in normalized:
        return "healthy"

    if "(unhealthy)" in normalized:
        return "unhealthy"

    if "health: starting" in normalized:
        return "starting"

    return None


def normalize_inspect_data(
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    """Normalize relevant fields from Docker inspect."""

    if not isinstance(payload, dict):
        return {
            "restart_count": None,
            "exit_code": None,
            "health": None,
        }

    state = payload.get("State", {})

    if not isinstance(state, dict):
        state = {}

    health_data = state.get("Health")

    health = None

    if isinstance(health_data, dict):
        health_value = health_data.get("Status")

        if isinstance(health_value, str):
            health = health_value.lower()

    restart_count = payload.get("RestartCount")

    try:
        normalized_restart_count = (
            int(restart_count)
            if restart_count is not None
            else None
        )
    except (TypeError, ValueError):
        normalized_restart_count = None

    exit_code = state.get("ExitCode")

    try:
        normalized_exit_code = (
            int(exit_code)
            if exit_code is not None
            else None
        )
    except (TypeError, ValueError):
        normalized_exit_code = None

    return {
        "restart_count": normalized_restart_count,
        "exit_code": normalized_exit_code,
        "health": health,
    }


def normalize_container(
    raw_container: dict[str, Any],
    inspect_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize Docker data into Guardian's container schema."""

    name = str(
        raw_container.get("Names")
        or raw_container.get("Name")
        or ""
    ).strip()

    image = str(
        raw_container.get("Image")
        or ""
    ).strip()

    state = str(
        raw_container.get("State")
        or ""
    ).strip().lower()

    status = str(
        raw_container.get("Status")
        or ""
    ).strip()

    ps_health = normalize_health(status)

    inspect_normalized = normalize_inspect_data(
        inspect_data
    )

    authoritative_health = inspect_normalized[
        "health"
    ]

    health = (
        authoritative_health
        if authoritative_health is not None
        else ps_health
    )

    return {
        "name": name or None,
        "image": image or None,
        "state": state or "unknown",
        "health": health,
        "status": status or None,
        "restart_count": inspect_normalized[
            "restart_count"
        ],
        "exit_code": inspect_normalized[
            "exit_code"
        ],
    }


def summarize_containers(
    containers: list[dict[str, Any]],
) -> dict[str, int]:
    """Return normalized Docker container counts."""

    running = 0
    stopped = 0
    healthy = 0
    unhealthy = 0
    restarting = 0
    paused = 0

    for container in containers:
        state = container.get("state")
        health = container.get("health")

        if state == "running":
            running += 1

        elif state in {
            "exited",
            "created",
            "dead",
        }:
            stopped += 1

        elif state == "restarting":
            restarting += 1

        elif state == "paused":
            paused += 1

        if health == "healthy":
            healthy += 1

        elif health == "unhealthy":
            unhealthy += 1

    return {
        "total": len(containers),
        "running": running,
        "stopped": stopped,
        "healthy": healthy,
        "unhealthy": unhealthy,
        "restarting": restarting,
        "paused": paused,
    }


def collect_docker_data() -> dict[str, Any]:
    """Collect normalized read-only Docker container information."""

    docker_result = run_docker_ps()

    if not docker_result["available"]:
        return {
            "available": False,
            "summary": {
                "total": 0,
                "running": 0,
                "stopped": 0,
                "healthy": 0,
                "unhealthy": 0,
                "restarting": 0,
                "paused": 0,
            },
            "containers": [],
            "inspection_errors": [],
            "error": docker_result["error"],
        }

    normalized: list[dict[str, Any]] = []
    inspection_errors: list[str] = []

    for raw_container in docker_result["containers"]:
        name = str(
            raw_container.get("Names")
            or raw_container.get("Name")
            or ""
        ).strip()

        inspect_payload = None

        if name:
            inspect_result = inspect_container(
                name
            )

            if inspect_result["available"]:
                inspect_payload = inspect_result[
                    "payload"
                ]
            else:
                inspection_errors.append(
                    f"{name}: "
                    f"{inspect_result['error']}"
                )

        normalized.append(
            normalize_container(
                raw_container,
                inspect_payload,
            )
        )

    return {
        "available": True,
        "summary": summarize_containers(
            normalized
        ),
        "containers": normalized,
        "inspection_errors": inspection_errors,
        "error": None,
    }


class DockerCollector:
    """Collect read-only Docker container status information."""

    name = "docker"

    def collect(self) -> CollectorResult:
        """Return Docker information as a standardized result."""

        data = collect_docker_data()

        if not data["available"]:
            return CollectorResult(
                name=self.name,
                status="UNAVAILABLE",
                available=False,
                data=data,
                error=data["error"],
            )

        return CollectorResult(
            name=self.name,
            status="COLLECTED",
            available=True,
            data=data,
            error=None,
        )

def add_restart_deltas(
    current_containers: list[dict[str, Any]],
    previous_report: dict[str, Any] | None,
) -> None:
    """Annotate containers with restart-count change since prior report."""

    previous_counts: dict[str, int] = {}

    if isinstance(previous_report, dict):
        previous_collectors = previous_report.get(
            "collectors",
            {},
        )

        if isinstance(previous_collectors, dict):
            previous_docker = previous_collectors.get(
                "docker",
                {},
            )

            if isinstance(previous_docker, dict):
                previous_data = previous_docker.get(
                    "data",
                    {},
                )

                if isinstance(previous_data, dict):
                    previous_containers = previous_data.get(
                        "containers",
                        [],
                    )

                    if isinstance(previous_containers, list):
                        for container in previous_containers:
                            if not isinstance(container, dict):
                                continue

                            name = container.get("name")
                            restart_count = container.get(
                                "restart_count"
                            )

                            if (
                                isinstance(name, str)
                                and isinstance(
                                    restart_count,
                                    int,
                                )
                            ):
                                previous_counts[
                                    name
                                ] = restart_count

    for container in current_containers:
        if not isinstance(container, dict):
            continue

        name = container.get("name")
        current_count = container.get(
            "restart_count"
        )

        if (
            not isinstance(name, str)
            or not isinstance(current_count, int)
        ):
            container["restart_delta"] = None
            continue

        previous_count = previous_counts.get(
            name
        )

        if previous_count is None:
            container["restart_delta"] = 0
            continue

        container["restart_delta"] = max(
            current_count - previous_count,
            0,
        )
