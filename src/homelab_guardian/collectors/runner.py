from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from homelab_guardian.collectors.base import Collector
from homelab_guardian.models import CollectorResult


LOGGER = logging.getLogger("homelab_guardian")


def run_collector(
    collector: Collector,
) -> CollectorResult:
    """Run one collector without allowing it to crash the application."""

    try:
        result = collector.collect()
    except Exception as error:
        LOGGER.exception(
            "Collector %s failed unexpectedly",
            collector.name,
        )

        return CollectorResult(
            name=collector.name,
            status="FAILED",
            available=False,
            data={},
            error=str(error),
        )

    if not isinstance(result, CollectorResult):
        return CollectorResult(
            name=collector.name,
            status="FAILED",
            available=False,
            data={},
            error=(
                "Collector returned an invalid result type: "
                f"{type(result).__name__}"
            ),
        )

    return result


def run_collectors(
    collectors: Iterable[Collector],
) -> dict[str, dict[str, Any]]:
    """Run multiple collectors and return results keyed by name."""

    results: dict[str, dict[str, Any]] = {}

    for collector in collectors:
        result = run_collector(collector)
        results[result.name] = result.to_dict()

    return results