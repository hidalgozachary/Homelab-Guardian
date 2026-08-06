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
        unraid.get_unraid_version(version_path)
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
        unraid.get_array_state(var_path)
        == "STARTED"
    )


def test_collect_unraid_data_on_non_unraid(
    tmp_path: Path,
) -> None:
    result = unraid.collect_unraid_data(
        version_path=tmp_path / "missing-version",
        var_path=tmp_path / "missing-var.ini",
    )

    assert result["available"] is False
    assert result["unraid_version"] is None
    assert result["array_state"] is None
    assert result["variables"] == {}
    assert result["collector_status"] == "NOT_UNRAID"
    assert result["error"] is None


def test_collect_unraid_data_on_unraid(
    tmp_path: Path,
) -> None:
    version_path = tmp_path / "unraid-version"
    var_path = tmp_path / "var.ini"

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
    assert result["unraid_version"] == "7.3.2"
    assert result["array_state"] == "STARTED"
    assert result["variables"]["mdNumDisks"] == "2"
    assert result["variables"]["mdInvalidDisk"] == "0"
    assert result["collector_status"] == "COLLECTED"


def test_unraid_collector_returns_unavailable(
    tmp_path: Path,
) -> None:
    collector = unraid.UnraidCollector(
        version_path=tmp_path / "missing-version",
        var_path=tmp_path / "missing-var.ini",
    )

    result = collector.collect()

    assert result.name == "unraid"
    assert result.status == "UNAVAILABLE"
    assert result.available is False
    assert result.data["collector_status"] == "NOT_UNRAID"
    assert result.error is None


def test_unraid_collector_returns_collected(
    tmp_path: Path,
) -> None:
    version_path = tmp_path / "unraid-version"
    var_path = tmp_path / "var.ini"

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
    assert result.data["unraid_version"] == "7.3.2"
    assert result.data["array_state"] == "STARTED"
    assert result.error is None