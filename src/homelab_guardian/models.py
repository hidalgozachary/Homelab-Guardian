from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CollectorResult:
    """Standard result returned by every Homelab Guardian collector."""

    name: str
    status: str
    available: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the collector result into a serializable dictionary."""

        return asdict(self)