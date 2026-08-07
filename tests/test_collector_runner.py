from homelab_guardian.collectors.runner import (
    run_collector,
    run_collectors,
)
from homelab_guardian.models import CollectorResult


class SuccessfulCollector:
    name = "successful"

    def collect(self) -> CollectorResult:
        return CollectorResult(
            name=self.name,
            status="COLLECTED",
            available=True,
            data={
                "value": 42,
            },
        )


class UnavailableCollector:
    name = "unavailable"

    def collect(self) -> CollectorResult:
        return CollectorResult(
            name=self.name,
            status="UNAVAILABLE",
            available=False,
            data={},
            error=None,
        )


class FailingCollector:
    name = "failing"

    def collect(self) -> CollectorResult:
        raise RuntimeError("collector exploded")


class InvalidCollector:
    name = "invalid"

    def collect(self) -> dict[str, object]:
        return {
            "status": "COLLECTED",
        }


def test_run_successful_collector() -> None:
    result = run_collector(SuccessfulCollector())

    assert result.name == "successful"
    assert result.status == "COLLECTED"
    assert result.available is True
    assert result.data == {"value": 42}
    assert result.error is None


def test_run_unavailable_collector() -> None:
    result = run_collector(UnavailableCollector())

    assert result.status == "UNAVAILABLE"
    assert result.available is False
    assert result.error is None


def test_runner_catches_collector_failure() -> None:
    result = run_collector(FailingCollector())

    assert result.name == "failing"
    assert result.status == "FAILED"
    assert result.available is False
    assert result.data == {}
    assert result.error == "collector exploded"


def test_runner_rejects_invalid_result_type() -> None:
    result = run_collector(InvalidCollector())

    assert result.status == "FAILED"
    assert result.available is False
    assert "invalid result type" in str(result.error)


def test_run_collectors_returns_results_by_name() -> None:
    results = run_collectors(
        [
            SuccessfulCollector(),
            UnavailableCollector(),
            FailingCollector(),
        ]
    )

    assert set(results) == {
        "successful",
        "unavailable",
        "failing",
    }

    assert results["successful"]["data"]["value"] == 42
    assert results["unavailable"]["status"] == "UNAVAILABLE"
    assert results["failing"]["status"] == "FAILED"