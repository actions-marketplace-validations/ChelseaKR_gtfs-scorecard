"""Tests for the versioned static public API builders (pure)."""

from __future__ import annotations

from typing import Any

from scorecard_pipeline.dataset import build_quality_dataset
from scorecard_pipeline.publicapi import (
    agencies_endpoint,
    api_index,
    build_api,
    by_state,
    leaderboard,
    stats_endpoint,
)


def _pt(date: str, score: float, grade: str) -> dict[str, Any]:
    return {
        "date": date,
        "score": score,
        "grade": grade,
        "categories": {},
        "days_until_expiry": 100,
    }


def _index() -> dict[str, Any]:
    return {
        "agencies": {
            "alpha": {"name": "Alpha Transit", "history": [_pt("2026-06-10", 90.0, "A")]},
            "bravo": {
                "name": "Bravo Transit",
                "history": [_pt("2026-06-08", 60.0, "D"), _pt("2026-06-10", 80.0, "B")],
            },
            "charlie": {
                "name": "Charlie Transit",
                "history": [_pt("2026-06-08", 75.0, "C"), _pt("2026-06-10", 55.0, "F")],
            },
        }
    }


def test_agencies_endpoint_is_the_flat_list() -> None:
    ds = build_quality_dataset(_index())
    ep = agencies_endpoint(ds)
    assert ep["count"] == 3
    assert {a["id"] for a in ep["agencies"]} == {"alpha", "bravo", "charlie"}


def test_leaderboard_ranks_and_finds_movers() -> None:
    idx = _index()
    board = leaderboard(idx, build_quality_dataset(idx))
    assert board["top"][0]["id"] == "alpha"  # 90 is highest
    assert board["bottom"][0]["id"] == "charlie"  # 55 is lowest
    # Bravo rose 60 -> 80; Charlie fell 75 -> 55.
    assert board["most_improved"][0]["id"] == "bravo"
    assert board["most_improved"][0]["score_delta"] == 20.0
    assert board["most_declined"][0]["id"] == "charlie"
    assert board["most_declined"][0]["score_delta"] == -20.0
    # Alpha has one history point, so it is not a mover.
    assert all(m["id"] != "alpha" for m in board["most_improved"])


def test_by_state_aggregates_with_unlocated_fallback() -> None:
    ds = build_quality_dataset(_index())
    out = by_state(ds, {"alpha": "California", "bravo": "California"})
    states = {s["state"]: s for s in out["states"]}
    assert states["California"]["count"] == 2
    assert states["California"]["median_score"] == 85.0  # median of 90, 80
    assert states["Unlocated"]["count"] == 1  # charlie has no state
    assert states["California"]["grade_distribution"]["A"] == 1


def test_stats_has_median_and_grade_distribution() -> None:
    ds = build_quality_dataset(_index())
    st = stats_endpoint(ds)
    assert st["agency_count"] == 3
    assert st["median_score"] == 80.0  # median of 90, 80, 55
    assert st["grade_distribution"]["A"] == 1
    assert st["grade_distribution"]["F"] == 1


def test_api_index_lists_endpoints_and_license() -> None:
    idx = api_index("https://example.org", "2026-06-21T00:00:00+00:00")
    assert idx["version"] == "v1"
    assert idx["endpoints"]["agencies"].endswith("/api/v1/agencies.json")
    assert "{agency_id}" in idx["endpoints"]["agency_detail"]
    assert idx["license"]


def test_build_api_returns_every_endpoint() -> None:
    api = build_api(
        _index(), states={"alpha": "California"}, base_url="https://x", generated_at="t"
    )
    assert set(api) == {
        "index.json",
        "agencies.json",
        "leaderboard.json",
        "by-state.json",
        "stats.json",
    }
