import json
import subprocess
from collections import namedtuple
from pathlib import Path

from homelab_guardian.collectors import storage


DiskUsage = namedtuple(
    "DiskUsage",
    [
        "total",
        "used",
        "free",
        "percent",
    ],
)

Partition = namedtuple(
    "Partition",
    [
        "device",
        "mountpoint",
        "fstype",
        "opts",
    ],
)


def test_bytes_to_gib() -> None:
    assert storage.bytes_to_gib(1024**3) == 1.0


def test_bytes_to_tib() -> None:
    assert storage.bytes_to_tib(1024**4) == 1.0


def test_find_mount_information_uses_most_specific_mount(
    tmp_path: Path,
) -> None:
    array_path = tmp_path / "mnt" / "user"
    array_path.mkdir(parents=True)

    partitions = [
        Partition(
            device="/dev/root",
            mountpoint="/",
            fstype="ext4",
            opts="rw",
        ),
        Partition(
            device="shfs",
            mountpoint=str(array_path),
            fstype="fuse.shfs",
            opts="rw,nosuid,nodev",
        ),
    ]

    result = storage.find_mount_information(
        path=array_path,
        partitions=partitions,
    )

    assert result["device"] == "shfs"
    assert result["mountpoint"] == str(array_path)
    assert result["filesystem"] == "fuse.shfs"
    assert result["mount_options"] == "rw,nosuid,nodev"


def test_find_mount_information_returns_empty_when_missing(
    tmp_path: Path,
) -> None:
    result = storage.find_mount_information(
        path=tmp_path,
        partitions=[],
    )

    assert result == {
        "device": None,
        "mountpoint": None,
        "filesystem": None,
        "mount_options": None,
    }


def test_collect_missing_filesystem_path(
    tmp_path: Path,
) -> None:
    result = storage.collect_filesystem_usage(
        tmp_path / "missing"
    )

    assert result["available"] is False
    assert result["filesystem"] is None
    assert result["percent"] is None
    assert result["error"] == "Path does not exist"


def test_collect_filesystem_usage(
    tmp_path: Path,
    monkeypatch,
) -> None:
    test_path = tmp_path / "array"
    test_path.mkdir()

    monkeypatch.setattr(
        storage.psutil,
        "disk_usage",
        lambda _path: DiskUsage(
            total=10 * 1024**3,
            used=2 * 1024**3,
            free=8 * 1024**3,
            percent=20.0,
        ),
    )

    monkeypatch.setattr(
        storage,
        "find_mount_information",
        lambda _path: {
            "device": "shfs",
            "mountpoint": str(test_path),
            "filesystem": "fuse.shfs",
            "mount_options": "rw",
        },
    )

    result = storage.collect_filesystem_usage(
        test_path
    )

    assert result["available"] is True
    assert result["device"] == "shfs"
    assert result["filesystem"] == "fuse.shfs"
    assert result["total_gib"] == 10.0
    assert result["used_gib"] == 2.0
    assert result["free_gib"] == 8.0
    assert result["percent"] == 20.0
    assert result["error"] is None


def test_collect_storage_data(
    tmp_path: Path,
    monkeypatch,
) -> None:
    array_path = tmp_path / "array"
    cache_path = tmp_path / "cache"

    array_path.mkdir()
    cache_path.mkdir()

    def fake_disk_usage(path: str) -> DiskUsage:
        if path == str(array_path):
            return DiskUsage(
                total=10 * 1024**3,
                used=2 * 1024**3,
                free=8 * 1024**3,
                percent=20.0,
            )

        return DiskUsage(
            total=100 * 1024**3,
            used=25 * 1024**3,
            free=75 * 1024**3,
            percent=25.0,
        )

    monkeypatch.setattr(
        storage.psutil,
        "disk_usage",
        fake_disk_usage,
    )

    monkeypatch.setattr(
        storage,
        "find_mount_information",
        lambda path: {
            "device": (
                "shfs"
                if path == array_path
                else "/dev/nvme0n1p1"
            ),
            "mountpoint": str(path),
            "filesystem": (
                "fuse.shfs"
                if path == array_path
                else "btrfs"
            ),
            "mount_options": "rw",
        },
    )

    result = storage.collect_storage_data(
        array_path=array_path,
        cache_path=cache_path,
    )

    assert result["array"]["percent"] == 20.0
    assert result["array"]["filesystem"] == "fuse.shfs"

    assert result["cache"]["percent"] == 25.0
    assert result["cache"]["filesystem"] == "btrfs"


def test_storage_collector_unavailable_when_paths_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        storage,
        "collect_disk_inventory",
        lambda: {
            "available": False,
            "devices": [],
            "error": "lsblk command is not available",
        },
    )

    collector = storage.StorageCollector(
        array_path=tmp_path / "missing-array",
        cache_path=tmp_path / "missing-cache",
    )

    result = collector.collect()

    assert result.name == "storage"
    assert result.status == "UNAVAILABLE"
    assert result.available is False
    assert result.error is None


def test_storage_collector_collected_when_array_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    array_path = tmp_path / "array"
    array_path.mkdir()

    monkeypatch.setattr(
        storage.psutil,
        "disk_usage",
        lambda _path: DiskUsage(
            total=10 * 1024**3,
            used=2 * 1024**3,
            free=8 * 1024**3,
            percent=20.0,
        ),
    )

    monkeypatch.setattr(
        storage,
        "find_mount_information",
        lambda path: {
            "device": "shfs",
            "mountpoint": str(path),
            "filesystem": "fuse.shfs",
            "mount_options": "rw",
        },
    )

    collector = storage.StorageCollector(
        array_path=array_path,
        cache_path=tmp_path / "missing-cache",
    )

    result = collector.collect()

    assert result.status == "COLLECTED"
    assert result.available is True
    assert result.data["array"]["available"] is True
    assert result.data["array"]["filesystem"] == "fuse.shfs"
    assert result.data["cache"]["available"] is False


def test_normalize_mountpoints() -> None:
    assert storage.normalize_mountpoints(None) == []
    assert storage.normalize_mountpoints("/boot") == ["/boot"]
    assert storage.normalize_mountpoints(
        ["/mnt/cache", None, ""]
    ) == ["/mnt/cache"]


def test_infer_device_role() -> None:
    assert storage.infer_device_role(["/boot"]) == "boot"
    assert storage.infer_device_role(["/mnt/cache"]) == "cache"
    assert storage.infer_device_role(["/mnt/disk1"]) == "array_disk"
    assert storage.infer_device_role(
        ["/mnt/remotes/example"]
    ) == "unassigned"
    assert storage.infer_device_role([]) == "unknown"


def test_flatten_lsblk_devices() -> None:
    raw_devices = [
        {
            "name": "sda",
            "kname": "sda",
            "path": "/dev/sda",
            "type": "disk",
            "size": 10 * 1024**4,
            "model": "Test HDD",
            "serial": "SERIAL1",
            "fstype": None,
            "mountpoints": [None],
            "children": [
                {
                    "name": "sda1",
                    "kname": "sda1",
                    "path": "/dev/sda1",
                    "type": "part",
                    "size": 10 * 1024**4,
                    "model": None,
                    "serial": None,
                    "fstype": "xfs",
                    "mountpoints": ["/mnt/disk1"],
                }
            ],
        }
    ]

    result = storage.flatten_lsblk_devices(
        raw_devices
    )

    assert len(result) == 2

    disk = result[0]
    partition = result[1]

    assert disk["path"] == "/dev/sda"
    assert disk["model"] == "Test HDD"
    assert disk["serial"] == "SERIAL1"
    assert disk["role"] == "unknown"

    assert partition["path"] == "/dev/sda1"
    assert partition["filesystem"] == "xfs"
    assert partition["mounted"] is True
    assert partition["role"] == "array_disk"


def test_collect_disk_inventory(
    monkeypatch,
) -> None:
    payload = {
        "blockdevices": [
            {
                "name": "nvme0n1",
                "kname": "nvme0n1",
                "path": "/dev/nvme0n1",
                "type": "disk",
                "size": 1024**4,
                "model": "WD Black",
                "serial": "NVME1",
                "fstype": None,
                "mountpoints": [None],
                "children": [
                    {
                        "name": "nvme0n1p1",
                        "kname": "nvme0n1p1",
                        "path": "/dev/nvme0n1p1",
                        "type": "part",
                        "size": 1024**4,
                        "model": None,
                        "serial": None,
                        "fstype": "btrfs",
                        "mountpoints": ["/mnt/cache"],
                    }
                ],
            }
        ]
    }

    monkeypatch.setattr(
        storage.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        ),
    )

    result = storage.collect_disk_inventory()

    assert result["available"] is True
    assert result["error"] is None
    assert len(result["devices"]) == 2
    assert result["devices"][1]["role"] == "cache"


def test_collect_disk_inventory_when_lsblk_missing(
    monkeypatch,
) -> None:
    def raise_missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(
        storage.subprocess,
        "run",
        raise_missing,
    )

    result = storage.collect_disk_inventory()

    assert result["available"] is False
    assert result["devices"] == []
    assert (
        result["error"]
        == "lsblk command is not available"
    )