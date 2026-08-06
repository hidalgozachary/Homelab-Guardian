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


def test_bytes_to_gib() -> None:
    assert storage.bytes_to_gib(1024**3) == 1.0


def test_bytes_to_tib() -> None:
    assert storage.bytes_to_tib(1024**4) == 1.0


def test_collect_missing_filesystem_path(
    tmp_path: Path,
) -> None:
    result = storage.collect_filesystem_usage(
        tmp_path / "missing"
    )

    assert result["available"] is False
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

    result = storage.collect_filesystem_usage(
        test_path
    )

    assert result["available"] is True
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

    result = storage.collect_storage_data(
        array_path=array_path,
        cache_path=cache_path,
    )

    assert result["array"]["percent"] == 20.0
    assert result["cache"]["percent"] == 25.0


def test_storage_collector_unavailable_when_paths_missing(
    tmp_path: Path,
) -> None:
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

    collector = storage.StorageCollector(
        array_path=array_path,
        cache_path=tmp_path / "missing-cache",
    )

    result = collector.collect()

    assert result.status == "COLLECTED"
    assert result.available is True
    assert result.data["array"]["available"] is True
    assert result.data["cache"]["available"] is False