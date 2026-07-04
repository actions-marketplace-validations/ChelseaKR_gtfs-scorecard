"""Tests for the high-cadence realtime archiving session."""

from __future__ import annotations

from pathlib import Path

import pytest

import scorecard_pipeline.rt_archiver as rt_archiver
import scorecard_pipeline.rt_health as rt_health
from scorecard_pipeline.config import Agency
from scorecard_pipeline.rt_archiver import MIN_INTERVAL_SECONDS, run_session, session_plan
from scorecard_pipeline.rt_health import RtObservation, load_observations


def test_session_plan_spaces_polls_over_the_window() -> None:
    assert session_plan(600, 20) == [i * 20 for i in range(31)]  # 0..600 inclusive
    assert session_plan(60, 20) == [0, 20, 40, 60]


def test_session_plan_enforces_minimum_interval() -> None:
    plan = session_plan(60, 1)  # 1s asked, clamped to the etiquette minimum
    assert plan[1] == MIN_INTERVAL_SECONDS


def test_session_plan_always_polls_once_and_caps() -> None:
    assert session_plan(0, 20) == [0]
    assert len(session_plan(10**6, 20)) <= rt_archiver.MAX_POLLS


def _agency() -> Agency:
    return Agency(
        id="demo",
        name="Demo",
        static_gtfs_url="https://x/gtfs.zip",
        rt_urls={"trip_updates": "https://x/tu.pb"},
    )


def test_run_session_records_one_observation_per_round(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rt_health, "repo_root", lambda: tmp_path)
    slept: list[float] = []
    polls = {"n": 0}

    def fake_poll(agency: Agency) -> RtObservation:
        polls["n"] += 1
        return RtObservation(
            ts=polls["n"], kinds_reachable=1, kinds_total=1, worst_lag_seconds=20, coverage_pct=None
        )

    recorded = run_session(
        _agency(),
        duration_seconds=60,
        interval_seconds=20,
        sleeper=lambda s: slept.append(s),
        poller=fake_poll,
    )
    assert recorded == 4  # offsets 0, 20, 40, 60
    assert polls["n"] == 4
    # Slept the gaps between rounds (not before the first).
    assert slept == [20, 20, 20]
    # Observations landed in the agency's record.
    assert len(load_observations("demo")) == 4


def test_run_session_skips_agency_without_realtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rt_health, "repo_root", lambda: tmp_path)
    no_rt = Agency(id="nort", name="No RT", static_gtfs_url="https://x/gtfs.zip")
    assert run_session(no_rt, duration_seconds=60, interval_seconds=20) == 0
