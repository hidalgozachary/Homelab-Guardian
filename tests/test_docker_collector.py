import json
import subprocess

from homelab_guardian.collectors import docker


def test_run_docker_ps_parses_json_lines(
    monkeypatch,
) -> None:
    output = "\n".join(
        [
            json.dumps(
                {
                    "Names": "UptimeKuma",
                    "Image": "louislam/uptime-kuma",
                    "State": "running",
                    "Status": "Up 2 days (healthy)",
                }
            ),
            json.dumps(
                {
                    "Names": "pihole",
                    "Image": "pihole/pihole:latest",
                    "State": "running",
                    "Status": "Up 2 days (healthy)",
                }
            ),
        ]
    )

    monkeypatch.setattr(
        docker.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=output,
            stderr="",
        ),
    )

    result = docker.run_docker_ps()

    assert result["available"] is True
    assert result["error"] is None
    assert len(result["containers"]) == 2
    assert result["containers"][0]["Names"] == "UptimeKuma"


def test_run_docker_ps_when_command_missing(
    monkeypatch,
) -> None:
    def raise_missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(
        docker.subprocess,
        "run",
        raise_missing,
    )

    result = docker.run_docker_ps()

    assert result["available"] is False
    assert result["containers"] == []
    assert result["error"] == "docker command is not available"


def test_inspect_container_returns_payload(
    monkeypatch,
) -> None:
    payload = {
        "Name": "/UptimeKuma",
        "RestartCount": 0,
        "State": {
            "Status": "running",
            "ExitCode": 0,
            "Health": {
                "Status": "healthy",
            },
        },
    }

    monkeypatch.setattr(
        docker.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        ),
    )

    result = docker.inspect_container(
        "UptimeKuma"
    )

    assert result["available"] is True
    assert result["payload"]["RestartCount"] == 0
    assert result["payload"]["State"]["ExitCode"] == 0
    assert (
        result["payload"]["State"]["Health"]["Status"]
        == "healthy"
    )


def test_inspect_container_when_missing(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        docker.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout="",
            stderr="No such container",
        ),
    )

    result = docker.inspect_container(
        "missing"
    )

    assert result["available"] is False
    assert result["payload"] is None
    assert result["error"] == "No such container"


def test_normalize_inspect_data() -> None:
    payload = {
        "RestartCount": 3,
        "State": {
            "ExitCode": 137,
            "Health": {
                "Status": "unhealthy",
            },
        },
    }

    result = docker.normalize_inspect_data(
        payload
    )

    assert result["restart_count"] == 3
    assert result["exit_code"] == 137
    assert result["health"] == "unhealthy"


def test_normalize_healthy_container() -> None:
    raw_container = {
        "Names": "UptimeKuma",
        "Image": "louislam/uptime-kuma",
        "State": "running",
        "Status": "Up 2 days (healthy)",
    }

    inspect_payload = {
        "RestartCount": 0,
        "State": {
            "ExitCode": 0,
            "Health": {
                "Status": "healthy",
            },
        },
    }

    result = docker.normalize_container(
        raw_container,
        inspect_payload,
    )

    assert result["name"] == "UptimeKuma"
    assert result["image"] == "louislam/uptime-kuma"
    assert result["state"] == "running"
    assert result["health"] == "healthy"
    assert result["restart_count"] == 0
    assert result["exit_code"] == 0


def test_normalize_container_uses_ps_health_fallback() -> None:
    raw_container = {
        "Names": "pihole",
        "Image": "pihole/pihole:latest",
        "State": "running",
        "Status": "Up 2 days (healthy)",
    }

    result = docker.normalize_container(
        raw_container,
        None,
    )

    assert result["health"] == "healthy"
    assert result["restart_count"] is None
    assert result["exit_code"] is None


def test_normalize_exited_container() -> None:
    raw_container = {
        "Names": "paperless",
        "Image": "paperless",
        "State": "exited",
        "Status": "Exited (137) 5 minutes ago",
    }

    inspect_payload = {
        "RestartCount": 2,
        "State": {
            "ExitCode": 137,
        },
    }

    result = docker.normalize_container(
        raw_container,
        inspect_payload,
    )

    assert result["state"] == "exited"
    assert result["health"] is None
    assert result["restart_count"] == 2
    assert result["exit_code"] == 137


def test_summarize_containers() -> None:
    containers = [
        {
            "name": "healthy",
            "state": "running",
            "health": "healthy",
        },
        {
            "name": "unhealthy",
            "state": "running",
            "health": "unhealthy",
        },
        {
            "name": "stopped",
            "state": "exited",
            "health": None,
        },
        {
            "name": "restarting",
            "state": "restarting",
            "health": None,
        },
        {
            "name": "paused",
            "state": "paused",
            "health": None,
        },
    ]

    result = docker.summarize_containers(
        containers
    )

    assert result["total"] == 5
    assert result["running"] == 2
    assert result["stopped"] == 1
    assert result["healthy"] == 1
    assert result["unhealthy"] == 1
    assert result["restarting"] == 1
    assert result["paused"] == 1


def test_collect_docker_data_with_inspection(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        docker,
        "run_docker_ps",
        lambda: {
            "available": True,
            "containers": [
                {
                    "Names": "UptimeKuma",
                    "Image": "louislam/uptime-kuma",
                    "State": "running",
                    "Status": "Up 2 days (healthy)",
                },
                {
                    "Names": "pihole",
                    "Image": "pihole/pihole:latest",
                    "State": "running",
                    "Status": "Up 2 days (healthy)",
                },
            ],
            "error": None,
        },
    )

    def fake_inspect(name):
        return {
            "available": True,
            "payload": {
                "RestartCount": 0,
                "State": {
                    "ExitCode": 0,
                    "Health": {
                        "Status": "healthy",
                    },
                },
            },
            "error": None,
        }

    monkeypatch.setattr(
        docker,
        "inspect_container",
        fake_inspect,
    )

    result = docker.collect_docker_data()

    assert result["available"] is True
    assert result["summary"]["total"] == 2
    assert result["summary"]["running"] == 2
    assert result["summary"]["healthy"] == 2
    assert result["summary"]["unhealthy"] == 0
    assert result["inspection_errors"] == []
    assert result["containers"][0]["restart_count"] == 0
    assert result["containers"][0]["exit_code"] == 0


def test_collect_docker_data_survives_inspect_failure(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        docker,
        "run_docker_ps",
        lambda: {
            "available": True,
            "containers": [
                {
                    "Names": "UptimeKuma",
                    "Image": "louislam/uptime-kuma",
                    "State": "running",
                    "Status": "Up 2 days (healthy)",
                }
            ],
            "error": None,
        },
    )

    monkeypatch.setattr(
        docker,
        "inspect_container",
        lambda _name: {
            "available": False,
            "payload": None,
            "error": "inspect failed",
        },
    )

    result = docker.collect_docker_data()

    assert result["available"] is True
    assert result["summary"]["total"] == 1
    assert result["summary"]["running"] == 1
    assert result["summary"]["healthy"] == 1
    assert len(result["inspection_errors"]) == 1
    assert "inspect failed" in result["inspection_errors"][0]


def test_docker_collector_unavailable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        docker,
        "collect_docker_data",
        lambda: {
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
            "error": "docker command is not available",
        },
    )

    collector = docker.DockerCollector()

    result = collector.collect()

    assert result.name == "docker"
    assert result.status == "UNAVAILABLE"
    assert result.available is False
    assert result.error == "docker command is not available"


def test_docker_collector_collected(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        docker,
        "collect_docker_data",
        lambda: {
            "available": True,
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
            "inspection_errors": [],
            "error": None,
        },
    )

    collector = docker.DockerCollector()

    result = collector.collect()

    assert result.name == "docker"
    assert result.status == "COLLECTED"
    assert result.available is True
    assert result.data["summary"]["running"] == 2

def test_add_restart_deltas_unchanged_count() -> None:
    current_containers = [
        {
            "name": "immich_server",
            "restart_count": 6,
        }
    ]

    previous_report = {
        "collectors": {
            "docker": {
                "data": {
                    "containers": [
                        {
                            "name": "immich_server",
                            "restart_count": 6,
                        }
                    ]
                }
            }
        }
    }

    docker.add_restart_deltas(
        current_containers,
        previous_report,
    )

    assert (
        current_containers[0]["restart_delta"]
        == 0
    )


def test_add_restart_deltas_detects_new_restart() -> None:
    current_containers = [
        {
            "name": "immich_server",
            "restart_count": 7,
        }
    ]

    previous_report = {
        "collectors": {
            "docker": {
                "data": {
                    "containers": [
                        {
                            "name": "immich_server",
                            "restart_count": 6,
                        }
                    ]
                }
            }
        }
    }

    docker.add_restart_deltas(
        current_containers,
        previous_report,
    )

    assert (
        current_containers[0]["restart_delta"]
        == 1
    )


def test_add_restart_deltas_without_previous_report() -> None:
    current_containers = [
        {
            "name": "pihole",
            "restart_count": 4,
        }
    ]

    docker.add_restart_deltas(
        current_containers,
        None,
    )

    assert (
        current_containers[0]["restart_delta"]
        == 0
    )


def test_add_restart_deltas_new_container_sets_baseline() -> None:
    current_containers = [
        {
            "name": "new_container",
            "restart_count": 3,
        }
    ]

    previous_report = {
        "collectors": {
            "docker": {
                "data": {
                    "containers": [
                        {
                            "name": "pihole",
                            "restart_count": 0,
                        }
                    ]
                }
            }
        }
    }

    docker.add_restart_deltas(
        current_containers,
        previous_report,
    )

    assert (
        current_containers[0]["restart_delta"]
        == 0
    )


def test_add_restart_deltas_handles_counter_reset() -> None:
    current_containers = [
        {
            "name": "immich_server",
            "restart_count": 0,
        }
    ]

    previous_report = {
        "collectors": {
            "docker": {
                "data": {
                    "containers": [
                        {
                            "name": "immich_server",
                            "restart_count": 6,
                        }
                    ]
                }
            }
        }
    }

    docker.add_restart_deltas(
        current_containers,
        previous_report,
    )

    assert (
        current_containers[0]["restart_delta"]
        == 0
    )