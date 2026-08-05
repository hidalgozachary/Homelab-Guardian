from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config/settings.json")


def load_settings(
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """Load and validate Homelab Guardian settings."""

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as config_file:
        settings = json.load(config_file)

    required_sections = {
        "guardian_name",
        "version",
        "warning_thresholds",
        "reports",
        "logging",
        "network",
        "notifications",
    }

    missing_sections = required_sections.difference(settings)

    if missing_sections:
        missing = ", ".join(sorted(missing_sections))
        raise ValueError(
            f"Configuration is missing required sections: {missing}"
        )

    return settings