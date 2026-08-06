from homelab_guardian.collectors import host


def test_format_uptime_with_days() -> None:
    uptime = host.format_uptime(
        6 * 86400 + 2 * 3600 + 13 * 60
    )

    assert uptime == "6 days, 2 hours, 13 minutes"


def test_format_uptime_with_one_hour() -> None:
    assert host.format_uptime(3600) == "1 hour"


def test_format_uptime_under_one_hour() -> None:
    assert host.format_uptime(12 * 60) == "12 minutes"


def test_cpu_temperature_returns_none_when_api_missing(
    monkeypatch,
) -> None:
    monkeypatch.delattr(
        host.psutil,
        "sensors_temperatures",
        raising=False,
    )

    assert host.get_cpu_temperature() is None


def test_collect_host_data(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        host,
        "get_cpu_model",
        lambda: "Test CPU",
    )

    monkeypatch.setattr(
        host,
        "get_cpu_temperature",
        lambda: 32.6,
    )

    monkeypatch.setattr(
        host,
        "get_load_average",
        lambda: (0.01, 0.02, 0.03),
    )

    monkeypatch.setattr(
        host,
        "get_uptime_seconds",
        lambda: 3600,
    )

    result = host.collect_host_data()

    assert result["hostname"]
    assert result["cpu"]["model"] == "Test CPU"
    assert result["cpu"]["temperature_celsius"] == 32.6
    assert result["load_average"] == (0.01, 0.02, 0.03)
    assert result["uptime"] == "1 hour"
    assert "memory" in result
    assert "swap" in result


def test_host_collector_returns_standard_result(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        host,
        "collect_host_data",
        lambda: {
            "hostname": "PandaServer",
            "uptime": "7 days",
        },
    )

    collector = host.HostCollector()
    result = collector.collect()

    assert result.name == "host"
    assert result.status == "COLLECTED"
    assert result.available is True
    assert result.data["hostname"] == "PandaServer"
    assert result.error is None