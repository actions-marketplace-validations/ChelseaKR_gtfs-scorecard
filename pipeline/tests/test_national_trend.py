"""Tests for the national quality trend (national_trend.py)."""

from __future__ import annotations

from typing import Any

from scorecard_pipeline.national_trend import as_of_points, top_improvers, trend_summary


def _index(agencies: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {"agencies": {aid: {"history": hist} for aid, hist in agencies.items()}}


def test_as_of_carries_forward_sparse_history() -> None:
    # b is only checked on day 1; on day 2 its day-1 score carries forward.
    idx = _index(
        {
            "a": [
                {"date": "2026-06-01", "score": 80.0, "grade": "B", "days_until_expiry": 50},
                {"date": "2026-06-02", "score": 90.0, "grade": "A", "days_until_expiry": 50},
            ],
            "b": [{"date": "2026-06-01", "score": 60.0, "grade": "D", "days_until_expiry": 50}],
        }
    )
    pts = as_of_points(idx)
    assert [p["date"] for p in pts] == ["2026-06-01", "2026-06-02"]
    # Day 1: (80 + 60) / 2 = 70.0
    assert pts[0]["average_score"] == 70.0
    assert pts[0]["agency_count"] == 2
    # Day 2: a=90 (new), b=60 (carried) -> 75.0
    assert pts[1]["average_score"] == 75.0
    assert pts[1]["agency_count"] == 2


def test_grade_distribution_and_expired_share() -> None:
    idx = _index(
        {
            "a": [{"date": "2026-06-01", "score": 90.0, "grade": "A", "days_until_expiry": 30}],
            "b": [{"date": "2026-06-01", "score": 50.0, "grade": "F", "days_until_expiry": -5}],
        }
    )
    p = as_of_points(idx)[0]
    assert p["grade_distribution"]["A"] == 1
    assert p["grade_distribution"]["F"] == 1
    # One of two feeds expired.
    assert p["expired_pct"] == 50.0


def test_agency_absent_before_first_check_not_counted() -> None:
    idx = _index(
        {
            "a": [
                {"date": "2026-06-01", "score": 80.0, "grade": "B", "days_until_expiry": 50},
                {"date": "2026-06-02", "score": 80.0, "grade": "B", "days_until_expiry": 50},
            ],
            "late": [{"date": "2026-06-02", "score": 40.0, "grade": "F", "days_until_expiry": 50}],
        }
    )
    # min_coverage=0 to test the raw carry-forward without the stable-cohort filter.
    pts = as_of_points(idx, min_coverage=0.0)
    # Day 1: only a exists.
    assert pts[0]["agency_count"] == 1
    assert pts[0]["average_score"] == 80.0
    # Day 2: both.
    assert pts[1]["agency_count"] == 2
    assert pts[1]["average_score"] == 60.0


def test_coverage_filter_drops_undercovered_early_dates() -> None:
    # Mirrors the real corpus: a tiny pilot cohort early, then the full set. The
    # early sparse dates must be dropped so a composition shift is not charted as a
    # quality decline.
    hist_full = [
        {"date": "2026-06-01", "score": 78.0, "grade": "C", "days_until_expiry": 50},
        {"date": "2026-06-02", "score": 60.0, "grade": "D", "days_until_expiry": 50},
    ]
    agencies: dict[str, list[dict[str, Any]]] = {"pilot": hist_full}
    # 100 agencies that only appear on day 2.
    for i in range(100):
        agencies[f"a{i}"] = [
            {"date": "2026-06-02", "score": 60.0, "grade": "D", "days_until_expiry": 50}
        ]
    pts = as_of_points(_index(agencies))
    # Day 1 had 1 of 101 feeds (under 80% of peak), so it is dropped.
    assert [p["date"] for p in pts] == ["2026-06-02"]
    assert pts[0]["agency_count"] == 101


def test_trend_summary_delta() -> None:
    idx = _index(
        {
            "a": [
                {"date": "2026-06-01", "score": 70.0, "grade": "C", "days_until_expiry": 50},
                {"date": "2026-06-03", "score": 76.0, "grade": "C", "days_until_expiry": 50},
            ],
        }
    )
    s = trend_summary(as_of_points(idx))
    assert s["points"] == 2
    assert s["score_delta"] == 6.0
    assert s["first"]["date"] == "2026-06-01"
    assert s["last"]["average_score"] == 76.0


def test_summary_neutral_with_one_point() -> None:
    idx = _index({"a": [{"date": "2026-06-01", "score": 70.0, "grade": "C"}]})
    s = trend_summary(as_of_points(idx))
    assert s["score_delta"] is None


def test_empty_index_is_safe() -> None:
    assert as_of_points({"agencies": {}}) == []
    assert trend_summary([]) == {"points": 0, "score_delta": None, "first": None, "last": None}


# ---------------------------------------------------------------------------
# top_improvers
# ---------------------------------------------------------------------------


def _imp_index(agencies: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Build an index where each value already has history + name."""
    return {"agencies": agencies}


def test_top_improvers_empty_index() -> None:
    assert top_improvers({"agencies": {}}) == []
    assert top_improvers({}) == []


def test_top_improvers_identifies_best_delta() -> None:
    # a improved by 20 points; b improved by 5; c declined.
    idx = _imp_index(
        {
            "a": {
                "name": "Alpha Transit",
                "history": [
                    {"date": "2026-04-01", "score": 50.0, "grade": "F"},
                    {"date": "2026-05-01", "score": 60.0, "grade": "D"},
                    {"date": "2026-06-01", "score": 70.0, "grade": "C"},
                ],
            },
            "b": {
                "name": "Beta Bus",
                "history": [
                    {"date": "2026-04-01", "score": 70.0, "grade": "C"},
                    {"date": "2026-05-01", "score": 72.0, "grade": "C"},
                    {"date": "2026-06-01", "score": 75.0, "grade": "B"},
                ],
            },
            "c": {
                "name": "Declining Depot",
                "history": [
                    {"date": "2026-04-01", "score": 80.0, "grade": "B"},
                    {"date": "2026-05-01", "score": 75.0, "grade": "B"},
                    {"date": "2026-06-01", "score": 70.0, "grade": "C"},
                ],
            },
        }
    )
    result = top_improvers(idx, window_days=90, min_checks=3, top=10)
    ids = [r["id"] for r in result]
    assert "a" in ids
    assert "b" in ids
    assert "c" not in ids, "Declined agency must not appear"
    assert ids[0] == "a", "Highest delta should be first"
    assert result[0]["delta"] == 20.0
    assert result[1]["delta"] == 5.0


def test_top_improvers_min_checks_excludes_sparse_agencies() -> None:
    # d has only 2 history points — below the default min_checks=3.
    idx = _imp_index(
        {
            "d": {
                "name": "Sparse Service",
                "history": [
                    {"date": "2026-04-01", "score": 40.0, "grade": "F"},
                    {"date": "2026-06-01", "score": 90.0, "grade": "A"},
                ],
            },
        }
    )
    result = top_improvers(idx, min_checks=3)
    assert result == [], "Agency with fewer than min_checks should be excluded"


def test_top_improvers_excludes_zero_and_negative_delta() -> None:
    idx = _imp_index(
        {
            "flat": {
                "name": "No Change",
                "history": [
                    {"date": "2026-04-01", "score": 60.0, "grade": "D"},
                    {"date": "2026-05-01", "score": 60.0, "grade": "D"},
                    {"date": "2026-06-01", "score": 60.0, "grade": "D"},
                ],
            },
            "down": {
                "name": "Getting Worse",
                "history": [
                    {"date": "2026-04-01", "score": 80.0, "grade": "B"},
                    {"date": "2026-05-01", "score": 75.0, "grade": "B"},
                    {"date": "2026-06-01", "score": 70.0, "grade": "C"},
                ],
            },
        }
    )
    result = top_improvers(idx, min_checks=3)
    assert result == [], "Flat or declining agencies must not appear"
