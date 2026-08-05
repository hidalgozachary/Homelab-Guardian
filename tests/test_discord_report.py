from homelab_guardian.reports.discord import (
    DISCORD_COLORS,
    build_discord_payload,
)


def test_healthy_discord_payload_uses_green_embed() -> None:
    report = {
        "timestamp": "2026-08-05T14:30:00-04:00",
        "cpu_percent": 5,
        "memory_percent": 5,
        "health": {
            "status": "HEALTHY",
            "score": 100,
            "issues": [],
        },
    }

    payload = build_discord_payload(
        report=report,
        report_title="PandaServer Operational Report",
        version="0.7.0",
    )

    embed = payload["embeds"][0]

    assert payload["username"] == "Homelab Guardian"
    assert (
        embed["title"]
        == "HEALTHY - PandaServer Operational Report"
    )
    assert embed["color"] == DISCORD_COLORS["HEALTHY"]
    assert "🐼 PandaServer Operational Report" in (
        embed["description"]
    )


def test_critical_discord_payload_uses_red_embed() -> None:
    report = {
        "timestamp": "2026-08-05T14:30:00-04:00",
        "cpu_percent": 99,
        "memory_percent": 99,
        "health": {
            "status": "CRITICAL",
            "score": 20,
            "issues": [
                "Docker service is not running",
            ],
        },
    }

    payload = build_discord_payload(
        report=report,
        report_title="PandaServer Operational Report",
        version="0.7.0",
    )

    embed = payload["embeds"][0]

    assert embed["color"] == DISCORD_COLORS["CRITICAL"]
    assert "🔴 OVERALL HEALTH" in embed["description"]
    assert "• Docker service is not running" in (
        embed["description"]
    )