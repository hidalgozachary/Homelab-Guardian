from __future__ import annotations

from typing import Protocol

from homelab_guardian.models import CollectorResult


class Collector(Protocol):
    """Interface implemented by Homelab Guardian collectors."""

    name: str

    def collect(self) -> CollectorResult:
        """Collect operational data and return a standard result."""
        ...