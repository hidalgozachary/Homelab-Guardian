from pathlib import Path

from homelab_guardian.collectors import unraid


def test_read_key_value_file(tmp_path: Path) -> None:
    test_file = tmp_path / "values.ini"

    test_file.write_text(
        '\n'.join(
            [
                'version="7.3.2"',
                "mdState=STARTED",
                "",
                "# comment",
            ]
        ),
        encoding="utf-8",
    )

    result = unraid.read_key_value_file(test_file)

    assert result["version"] == "7.3.2"
    assert result["mdState"] == "STARTED"


def test_read_missing_key_value_file_returns_empty_dict(
    tmp_path: Path,
) -> None:
    result = unraid.read_key_value_file(
        tmp_path / "missing.ini"
    )

    assert result == {}


def test_format_uptime_with_days() -> None:
    uptime = unraid.format_uptime(
        6 * 86400 + 2 * 3600 + 13 * 60
    )

    assert uptime == "6 days, 2 hours, 13 minutes"


def test_format_uptime_under_one_hour() -> None:
    assert unraid.format_uptime(12 * 60) == "12 minutes"


def test_collect_unraid_host_on_non_unraid(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        unraid,
        "detect_unraid",
        lambda: False,
    )

    monkeypatch.setattr(
        unraid,
        "get_uptime_seconds",
        lambda: 3600,
    )

    monkeypatch.setattr(
        unraid,
        "get_load_average",
        lambda: (0.1, 0.2, 0.3),
    )

    monkeypatch.setattr(
        unraid,
        "get_cpu_temperature",
        lambda: None,
    )

    result = unraid.collect_unraid_host()

    assert result["available"] is False
    assert result["collector_status"] == "NOT_UNRAID"
    assert result["unraid_version"] is None
    assert result["array_state"] is None
    assert result["uptime"] == "1 hour"


def test_collect_unraid_host_on_unraid(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        unraid,
        "detect_unraid",
        lambda: True,
    )

    monkeypatch.setattr(
        unraid,
        "get_unraid_version",
        lambda: "7.3.2",
    )

    monkeypatch.setattr(
        unraid,
        "get_array_state",
        lambda: "STARTED",
    )

    monkeypatch.setattr(
        unraid,
        "get_uptime_seconds",
        lambda: 600,
    )

    monkeypatch.setattr(
        unraid,
        "get_load_average",
        lambda: (0.0, 0.02, 0.01),
    )

    monkeypatch.setattr(
        unraid,
        "get_cpu_temperature",
        lambda: 32.6,
    )

    result = unraid.collect_unraid_host()

    assert result["available"] is True
    assert result["platform"] == "Unraid"
    assert result["unraid_version"] == "7.3.2"
    assert result["array_state"] == "STARTED"
    assert result["cpu_temperature"] == 32.6
    assert result["collector_status"] == "COLLECTED"

def test_cpu_temperature_returns_none_when_api_missing(
    monkeypatch,
) -> None:
    monkeypatch.delattr(
        unraid.psutil,
        "sensors_temperatures",
        raising=False,
    )

    assert unraid.get_cpu_temperature() is None

def test_unraid_collector_returns_unavailable_on_mac(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        unraid,
        "collect_unraid_host",
        lambda: {
            "available": False,
            "collector_status": "NOT_UNRAID",
        },
    )

    collector = unraid.UnraidCollector()
    result = collector.collect()

    assert result.name == "unraid"
    assert result.status == "UNAVAILABLE"
    assert result.available is False
    assert result.data["collector_status"] == "NOT_UNRAID"
    assert result.error is None


def test_unraid_collector_returns_collected_on_unraid(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        unraid,
        "collect_unraid_host",
        lambda: {
            "available": True,
            "collector_status": "COLLECTED",
            "unraid_version": "7.3.2",
            "array_state": "STARTED",
        },
    )

    collector = unraid.UnraidCollector()
    result = collector.collect()

    assert result.name == "unraid"
    assert result.status == "COLLECTED"
    assert result.available is True
    assert result.data["unraid_version"] == "7.3.2"
    assert result.data["array_state"] == "STARTED"
    assert result.error is None