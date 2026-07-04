"""Tests for CLI helpers that don't require fetching or the Java validator."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from scorecard_pipeline.cli import _try_gate


def _artifact(grade: str, days: int | None) -> dict:  # type: ignore[type-arg]
    return {
        "overall": {"grade": grade, "score": 0},
        "categories": {"freshness": {"details": {"days_until_expiry": days}}},
    }


def _args(min_grade: str | None = None, min_days: int | None = None) -> argparse.Namespace:
    return argparse.Namespace(min_grade=min_grade, min_days_to_expiry=min_days)


def test_gate_passes_without_thresholds() -> None:
    assert _try_gate(_artifact("F", -5), _args()) == 0


def test_gate_fails_below_min_grade() -> None:
    assert _try_gate(_artifact("C", 90), _args(min_grade="B")) == 1
    assert _try_gate(_artifact("B", 90), _args(min_grade="B")) == 0
    assert _try_gate(_artifact("A", 90), _args(min_grade="B")) == 0


def test_gate_fails_when_expiring_too_soon() -> None:
    assert _try_gate(_artifact("A", 10), _args(min_days=30)) == 1
    assert _try_gate(_artifact("A", 45), _args(min_days=30)) == 0
    assert _try_gate(_artifact("A", None), _args(min_days=30)) == 1  # no expiry date fails


def test_gate_combines_thresholds() -> None:
    # Grade ok but expiring too soon still fails.
    assert _try_gate(_artifact("A", 5), _args(min_grade="B", min_days=30)) == 1


def test_prune_reports_orphans_without_deleting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from scorecard_pipeline import cli

    art = tmp_path / "data" / "artifacts"
    (art / "still-here").mkdir(parents=True)
    (art / "long-gone").mkdir()
    monkeypatch.setenv("SCORECARD_ROOT", str(tmp_path))
    monkeypatch.setattr(cli, "AGENCIES", {"still-here": object()})
    parser = argparse.ArgumentParser()

    args = argparse.Namespace(delete=False)
    assert cli._cmd_prune(args, parser) == 0
    out = capsys.readouterr().out
    assert "orphan\tlong-gone" in out
    assert "Report only" in out
    assert (art / "long-gone").exists()  # never deletes without --delete

    args = argparse.Namespace(delete=True)
    assert cli._cmd_prune(args, parser) == 0
    assert not (art / "long-gone").exists()
    assert (art / "still-here").exists()
