import subprocess

from homelab_guardian.collectors import kernel


def test_run_dmesg_success(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        kernel.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="kernel log",
            stderr="",
        ),
    )

    result = kernel.run_dmesg()

    assert result["available"] is True
    assert result["output"] == "kernel log"
    assert result["error"] is None


def test_run_dmesg_failure(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        kernel.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout="",
            stderr="Operation not permitted",
        ),
    )

    result = kernel.run_dmesg()

    assert result["available"] is False
    assert result["error"] == "Operation not permitted"


def test_classify_kernel_events() -> None:
    output = """
kernel: BUG: unable to handle page fault
kernel: Out of memory: Killed process 1234
kernel: BTRFS error (device nvme0n1p1)
kernel: nvme nvme0: I/O timeout
kernel: EDAC MC0: 1 CE memory error
"""

    result = kernel.classify_kernel_events(
        output
    )

    assert result["total_events"] >= 5

    assert len(
        result["events"]["kernel_fault"]
    ) >= 1

    assert len(
        result["events"]["oom"]
    ) >= 1

    assert len(
        result["events"]["btrfs_error"]
    ) >= 1

    assert len(
        result["events"]["nvme_error"]
    ) >= 1

    assert len(
        result["events"]["hardware_error"]
    ) >= 1


def test_kernel_collector_unavailable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        kernel,
        "run_dmesg",
        lambda: {
            "available": False,
            "output": "",
            "error": "Operation not permitted",
        },
    )

    collector = kernel.KernelHealthCollector()

    result = collector.collect()

    assert result.name == "kernel_health"
    assert result.status == "UNAVAILABLE"
    assert result.available is False


def test_kernel_collector_collected(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        kernel,
        "run_dmesg",
        lambda: {
            "available": True,
            "output": "",
            "error": None,
        },
    )

    collector = kernel.KernelHealthCollector()

    result = collector.collect()

    assert result.name == "kernel_health"
    assert result.status == "COLLECTED"
    assert result.available is True
    assert result.data["total_events"] == 0