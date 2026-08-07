from pathlib import Path

from homelab_guardian.collectors import unraid


def test_read_key_value_file(tmp_path: Path) -> None:
    test_file = tmp_path / "values.ini"

    test_file.write_text(
        "\n".join(
            [
                'version="7.3.2"',
                "mdState=STARTED",
                "",
                "# comment",
                "invalid-line",
            ]
        ),
        encoding="utf-8",
    )

    result = unraid.read_key_value_file(test_file)

    assert result["version"] == "7.3.2"
    assert result["mdState"] == "STARTED"
    assert "invalid-line" not in result


def test_read_missing_key_value_file_returns_empty_dict(
    tmp_path: Path,
) -> None:
    result = unraid.read_key_value_file(
        tmp_path / "missing.ini"
    )

    assert result == {}


def test_detect_unraid_when_version_file_exists(
    tmp_path: Path,
) -> None:
    version_path = tmp_path / "unraid-version"

    version_path.write_text(
        'version="7.3.2"\n',
        encoding="utf-8",
    )

    assert unraid.detect_unraid(version_path) is True


def test_detect_unraid_when_version_file_missing(
    tmp_path: Path,
) -> None:
    assert (
        unraid.detect_unraid(
            tmp_path / "missing-version"
        )
        is False
    )


def test_get_unraid_version(
    tmp_path: Path,
) -> None:
    version_path = tmp_path / "unraid-version"

    version_path.write_text(
        'version="7.3.2"\n',
        encoding="utf-8",
    )

    assert (
        unraid.get_unraid_version(
            version_path
        )
        == "7.3.2"
    )


def test_get_array_state(
    tmp_path: Path,
) -> None:
    var_path = tmp_path / "var.ini"

    var_path.write_text(
        "mdState=STARTED\n",
        encoding="utf-8",
    )

    assert (
        unraid.get_array_state(
            var_path
        )
        == "STARTED"
    )


def test_collect_unraid_data_on_non_unraid(
    tmp_path: Path,
) -> None:
    result = unraid.collect_unraid_data(
        version_path=(
            tmp_path / "missing-version"
        ),
        var_path=(
            tmp_path / "missing-var.ini"
        ),
    )

    assert result["available"] is False
    assert result["unraid_version"] is None
    assert result["array_state"] is None

    assert (
        result["disk_assignments"]
        == {}
    )

    assert "variables" not in result

    assert (
        result["collector_status"]
        == "NOT_UNRAID"
    )

    assert result["error"] is None


def test_collect_unraid_data_on_unraid(
    tmp_path: Path,
) -> None:
    version_path = (
        tmp_path / "unraid-version"
    )

    var_path = (
        tmp_path / "var.ini"
    )

    version_path.write_text(
        'version="7.3.2"\n',
        encoding="utf-8",
    )

    var_path.write_text(
        "\n".join(
            [
                "mdState=STARTED",
                "mdNumDisks=2",
                "mdInvalidDisk=0",
                "mdMissingDisk=0",
            ]
        ),
        encoding="utf-8",
    )

    result = unraid.collect_unraid_data(
        version_path=version_path,
        var_path=var_path,
    )

    assert result["available"] is True

    assert (
        result["unraid_version"]
        == "7.3.2"
    )

    assert (
        result["array_state"]
        == "STARTED"
    )

    assert isinstance(
        result["disk_assignments"],
        dict,
    )

    assert "variables" not in result

    assert (
        result["collector_status"]
        == "COLLECTED"
    )

    assert result["error"] is None


def test_unraid_collector_returns_unavailable(
    tmp_path: Path,
) -> None:
    collector = unraid.UnraidCollector(
        version_path=(
            tmp_path / "missing-version"
        ),
        var_path=(
            tmp_path / "missing-var.ini"
        ),
    )

    result = collector.collect()

    assert result.name == "unraid"
    assert result.status == "UNAVAILABLE"
    assert result.available is False

    assert (
        result.data["collector_status"]
        == "NOT_UNRAID"
    )

    assert "variables" not in result.data
    assert result.error is None


def test_unraid_collector_returns_collected(
    tmp_path: Path,
) -> None:
    version_path = (
        tmp_path / "unraid-version"
    )

    var_path = (
        tmp_path / "var.ini"
    )

    version_path.write_text(
        'version="7.3.2"\n',
        encoding="utf-8",
    )

    var_path.write_text(
        "mdState=STARTED\n",
        encoding="utf-8",
    )

    collector = unraid.UnraidCollector(
        version_path=version_path,
        var_path=var_path,
    )

    result = collector.collect()

    assert result.name == "unraid"
    assert result.status == "COLLECTED"
    assert result.available is True

    assert (
        result.data["unraid_version"]
        == "7.3.2"
    )

    assert (
        result.data["array_state"]
        == "STARTED"
    )

    assert "variables" not in result.data
    assert result.error is None


def test_read_sectioned_key_value_file(
    tmp_path: Path,
) -> None:
    disks_path = (
        tmp_path / "disks.ini"
    )

    disks_path.write_text(
        "\n".join(
            [
                '["parity"]',
                'device="sdb"',
                'id="PARITY123"',
                'type="Parity"',
                'status="DISK_OK"',
                "",
                '["disk1"]',
                'device="sdc"',
                'id="DATA123"',
                'type="Data"',
            ]
        ),
        encoding="utf-8",
    )

    result = (
        unraid.read_sectioned_key_value_file(
            disks_path
        )
    )

    assert (
        result["parity"]["device"]
        == "sdb"
    )

    assert (
        result["parity"]["id"]
        == "PARITY123"
    )

    assert (
        result["disk1"]["device"]
        == "sdc"
    )

    assert (
        result["disk1"]["type"]
        == "Data"
    )


def test_normalize_disk_role() -> None:
    assert (
        unraid.normalize_disk_role(
            "parity"
        )
        == "parity"
    )

    assert (
        unraid.normalize_disk_role(
            "parity2"
        )
        == "parity2"
    )

    assert (
        unraid.normalize_disk_role(
            "disk1"
        )
        == "array_disk"
    )

    assert (
        unraid.normalize_disk_role(
            "disk30"
        )
        == "array_disk"
    )

    assert (
        unraid.normalize_disk_role(
            "cache"
        )
        == "cache"
    )

    assert (
        unraid.normalize_disk_role(
            "flash"
        )
        == "flash"
    )

    assert (
        unraid.normalize_disk_role(
            "something"
        )
        == "unknown"
    )


def test_get_disk_assignments(
    tmp_path: Path,
) -> None:
    disks_path = (
        tmp_path / "disks.ini"
    )

    disks_path.write_text(
        "\n".join(
            [
                '["parity"]',
                'device="sdb"',
                'id="PARITY123"',
                'size="9766436812"',
                'type="Parity"',
                'status="DISK_OK"',
                'temp="39"',
                'numErrors="0"',
                "",
                '["disk1"]',
                'device="sdc"',
                'id="DATA123"',
                'size="9766303744"',
                'type="Data"',
                'status="DISK_OK"',
                'temp="38"',
                'numErrors="0"',
                'fsType="xfs"',
                'fsStatus="Mounted"',
                'fsMountpoint="/mnt/disk1"',
                "",
                '["parity2"]',
                'device=""',
                'id=""',
                'size="0"',
                'type="Parity"',
                'status="DISK_NP_DSBL"',
                'temp="*"',
                'numErrors="0"',
                "",
                '["cache"]',
                'device="nvme0n1"',
                'id="CACHE123"',
                'size="976761560"',
                'type="Cache"',
                'status="DISK_OK"',
                'temp="44"',
                'numErrors="0"',
                'fsType="btrfs"',
                'fsStatus="Mounted"',
                'fsMountpoint="/mnt/cache"',
                "",
                '["flash"]',
                'device="sda"',
                'id="FLASH123"',
                'size="15312896"',
                'type="Flash"',
                'status="DISK_OK"',
                'temp="*"',
                'numErrors="0"',
                'fsType="vfat"',
                'fsStatus="Mounted"',
                'fsMountpoint="/boot"',
            ]
        ),
        encoding="utf-8",
    )

    result = (
        unraid.get_disk_assignments(
            disks_path
        )
    )

    assert (
        result["parity"]["role"]
        == "parity"
    )

    assert (
        result["parity"]["assigned"]
        is True
    )

    assert (
        result["parity"]["device"]
        == "sdb"
    )

    assert (
        result["parity"][
            "temperature_celsius"
        ]
        == 39
    )

    assert (
        result["parity"]["errors"]
        == 0
    )

    assert (
        result["disk1"]["role"]
        == "array_disk"
    )

    assert (
        result["disk1"]["assigned"]
        is True
    )

    assert (
        result["disk1"]["device"]
        == "sdc"
    )

    assert (
        result["disk1"]["filesystem"]
        == "xfs"
    )

    assert (
        result["disk1"][
            "filesystem_status"
        ]
        == "Mounted"
    )

    assert (
        result["disk1"]["mountpoint"]
        == "/mnt/disk1"
    )

    assert (
        result["parity2"]["role"]
        == "parity2"
    )

    assert (
        result["parity2"]["assigned"]
        is False
    )

    assert (
        result["parity2"]["device"]
        is None
    )

    assert (
        result["parity2"][
            "temperature_celsius"
        ]
        is None
    )

    assert (
        result["cache"]["role"]
        == "cache"
    )

    assert (
        result["cache"]["assigned"]
        is True
    )

    assert (
        result["cache"]["device"]
        == "nvme0n1"
    )

    assert (
        result["cache"][
            "temperature_celsius"
        ]
        == 44
    )

    assert (
        result["flash"]["role"]
        == "flash"
    )

    assert (
        result["flash"]["assigned"]
        is True
    )

    assert (
        result["flash"]["device"]
        == "sda"
    )

    assert (
        result["flash"][
            "temperature_celsius"
        ]
        is None
    )