from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from homelab_guardian.reports.json_report import (
    find_previous_report,
    load_json_report,
    prune_old_reports,
    save_json_report,
)


def test_save_json_report(
    tmp_path: Path,
) -> None:
    report = {
        "health": {
            "status": "HEALTHY",
            "score": 100,
        }
    }

    report_path = save_json_report(
        report,
        str(tmp_path),
    )

    assert report_path.exists()

    payload = json.loads(
        report_path.read_text(
            encoding="utf-8"
        )
    )

    assert payload == report

    assert (
        report_path.name.startswith(
            "health_report_"
        )
    )

    assert (
        report_path.suffix
        == ".json"
    )


def test_find_previous_report_returns_newest(
    tmp_path: Path,
) -> None:
    older = (
        tmp_path
        / "health_report_20260801_120000.json"
    )

    newer = (
        tmp_path
        / "health_report_20260802_120000.json"
    )

    older.write_text(
        "{}",
        encoding="utf-8",
    )

    newer.write_text(
        "{}",
        encoding="utf-8",
    )

    os.utime(
        older,
        (
            1000,
            1000,
        ),
    )

    os.utime(
        newer,
        (
            2000,
            2000,
        ),
    )

    result = find_previous_report(
        str(tmp_path)
    )

    assert result == newer


def test_find_previous_report_missing_directory(
    tmp_path: Path,
) -> None:
    result = find_previous_report(
        str(
            tmp_path
            / "missing"
        )
    )

    assert result is None


def test_load_json_report(
    tmp_path: Path,
) -> None:
    report_path = (
        tmp_path
        / "health_report_test.json"
    )

    report_path.write_text(
        json.dumps(
            {
                "health": {
                    "status": "HEALTHY",
                }
            }
        ),
        encoding="utf-8",
    )

    result = load_json_report(
        report_path
    )

    assert result == {
        "health": {
            "status": "HEALTHY",
        }
    }


def test_load_json_report_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    report_path = (
        tmp_path
        / "health_report_bad.json"
    )

    report_path.write_text(
        "{not-json",
        encoding="utf-8",
    )

    assert (
        load_json_report(
            report_path
        )
        is None
    )


def test_prune_old_reports(
    tmp_path: Path,
) -> None:
    now = datetime(
        2026,
        8,
        18,
        12,
        0,
        0,
    )

    old_report = (
        tmp_path
        / "health_report_old.json"
    )

    recent_report = (
        tmp_path
        / "health_report_recent.json"
    )

    unrelated_file = (
        tmp_path
        / "notes.json"
    )

    old_report.write_text(
        "{}",
        encoding="utf-8",
    )

    recent_report.write_text(
        "{}",
        encoding="utf-8",
    )

    unrelated_file.write_text(
        "{}",
        encoding="utf-8",
    )

    old_time = (
        now
        - timedelta(
            days=31
        )
    ).timestamp()

    recent_time = (
        now
        - timedelta(
            days=29
        )
    ).timestamp()

    os.utime(
        old_report,
        (
            old_time,
            old_time,
        ),
    )

    os.utime(
        recent_report,
        (
            recent_time,
            recent_time,
        ),
    )

    deleted = prune_old_reports(
        str(tmp_path),
        retention_days=30,
        now=now,
    )

    assert old_report in deleted
    assert old_report.exists() is False

    assert recent_report.exists() is True
    assert unrelated_file.exists() is True


def test_prune_old_reports_ignores_invalid_retention(
    tmp_path: Path,
) -> None:
    report_path = (
        tmp_path
        / "health_report_old.json"
    )

    report_path.write_text(
        "{}",
        encoding="utf-8",
    )

    deleted = prune_old_reports(
        str(tmp_path),
        retention_days=0,
    )

    assert deleted == []
    assert report_path.exists() is True