import json
import subprocess

from homelab_guardian.collectors import smart


def test_run_smartctl_returns_json(
    monkeypatch,
) -> None:
    payload = {
        "device": {
            "name": "/dev/sdb",
            "protocol": "ATA",
        },
        "smart_status": {
            "passed": True,
        },
    }

    monkeypatch.setattr(
        smart.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        ),
    )

    result = smart.run_smartctl("/dev/sdb")

    assert result["available"] is True
    assert result["payload"]["smart_status"]["passed"] is True
    assert result["error"] is None


def test_run_smartctl_when_command_missing(
    monkeypatch,
) -> None:
    def raise_missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(
        smart.subprocess,
        "run",
        raise_missing,
    )

    result = smart.run_smartctl("/dev/sdb")

    assert result["available"] is False
    assert result["payload"] is None
    assert result["error"] == "smartctl command is not available"


def test_normalize_ata_smart_data() -> None:
    payload = {
        "device": {
            "name": "/dev/sdb",
            "protocol": "ATA",
        },
        "smart_status": {
            "passed": True,
        },
        "temperature": {
            "current": 39,
        },
        "power_on_time": {
            "hours": 2962,
        },
        "ata_smart_attributes": {
            "table": [
                {
                    "name": "Reallocated_Sector_Ct",
                    "raw": {
                        "value": 0,
                    },
                },
                {
                    "name": "Current_Pending_Sector",
                    "raw": {
                        "value": 0,
                    },
                },
                {
                    "name": "Offline_Uncorrectable",
                    "raw": {
                        "value": 0,
                    },
                },
                {
                    "name": "UDMA_CRC_Error_Count",
                    "raw": {
                        "value": 0,
                    },
                },
            ]
        },
    }

    result = smart.normalize_smart_data(
        payload
    )

    assert result["device"] == "/dev/sdb"
    assert result["protocol"] == "ATA"
    assert result["passed"] is True
    assert result["status"] == "PASSED"
    assert result["temperature_celsius"] == 39
    assert result["power_on_hours"] == 2962
    assert result["reallocated_sectors"] == 0
    assert result["pending_sectors"] == 0
    assert result["uncorrectable_sectors"] == 0
    assert result["crc_errors"] == 0
    assert result["media_errors"] is None


def test_normalize_nvme_smart_data() -> None:
    payload = {
        "device": {
            "name": "/dev/nvme0n1",
            "protocol": "NVMe",
        },
        "smart_status": {
            "passed": True,
        },
        "temperature": {
            "current": 44,
        },
        "power_on_time": {
            "hours": 3626,
        },
        "nvme_smart_health_information_log": {
            "critical_warning": 0,
            "percentage_used": 0,
            "media_errors": 0,
        },
    }

    result = smart.normalize_smart_data(
        payload
    )

    assert result["device"] == "/dev/nvme0n1"
    assert result["protocol"] == "NVMe"
    assert result["passed"] is True
    assert result["status"] == "PASSED"
    assert result["temperature_celsius"] == 44
    assert result["power_on_hours"] == 3626
    assert result["media_errors"] == 0
    assert result["percentage_used"] == 0
    assert result["critical_warning"] == 0
    assert result["reallocated_sectors"] is None


def test_collect_smart_for_assignments(
    monkeypatch,
) -> None:
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
        "parity2": {
            "assigned": False,
            "role": "parity2",
            "device": None,
        },
        "flash": {
            "assigned": True,
            "role": "flash",
            "device": "sda",
        },
    }

    payload = {
        "device": {
            "name": "/dev/example",
            "protocol": "ATA",
        },
        "smart_status": {
            "passed": True,
        },
    }

    monkeypatch.setattr(
        smart,
        "run_smartctl",
        lambda device: {
            "available": True,
            "payload": {
                **payload,
                "device": {
                    "name": device,
                    "protocol": "ATA",
                },
            },
            "error": None,
        },
    )

    result = smart.collect_smart_for_assignments(
        assignments
    )

    assert set(result) == {
        "parity",
        "disk1",
    }

    assert result["parity"]["device"] == "/dev/sdb"
    assert result["disk1"]["device"] == "/dev/sdc"


def test_smart_collector_unavailable_without_devices() -> None:
    collector = smart.SmartCollector(
        assignments={}
    )

    result = collector.collect()

    assert result.name == "smart"
    assert result.status == "UNAVAILABLE"
    assert result.available is False
    assert result.data == {}


def test_smart_collector_collected(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        smart,
        "collect_smart_for_assignments",
        lambda _assignments: {
            "parity": {
                "available": True,
                "device": "/dev/sdb",
                "smart": {
                    "status": "PASSED",
                },
                "error": None,
            }
        },
    )

    collector = smart.SmartCollector(
        assignments={
            "parity": {
                "assigned": True,
                "role": "parity",
                "device": "sdb",
            }
        }
    )

    result = collector.collect()

    assert result.name == "smart"
    assert result.status == "COLLECTED"
    assert result.available is True
    assert result.data["parity"]["smart"]["status"] == "PASSED"