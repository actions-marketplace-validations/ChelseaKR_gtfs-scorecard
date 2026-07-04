"""Tests for the feed time-machine history narrative (pure)."""

from __future__ import annotations

from typing import Any

from scorecard_pipeline.timemachine import history_events


def _pt(date: str, score: float, grade: str, days: int | None, **cats: float) -> dict[str, Any]:
    return {
        "date": date,
        "score": score,
        "grade": grade,
        "days_until_expiry": days,
        "categories": cats,
    }


def test_grade_change_names_the_driving_category_and_sorts_newest_first() -> None:
    history = [
        _pt("2026-06-10", 84.0, "B", 80, correctness=90.0, freshness=85.0),
        _pt("2026-06-14", 70.0, "C", 78, correctness=90.0, freshness=40.0),
        _pt("2026-06-16", 84.0, "B", 76, correctness=90.0, freshness=85.0),
    ]
    events = history_events(history)
    # Newest first: the recovery, then the dip.
    assert [e.date for e in events] == ["2026-06-16", "2026-06-14"]
    assert events[1].kind == "grade_change"
    assert "Grade went B to C" in events[1].detail
    assert "freshness fell 45 points" in events[1].detail


def test_expiry_window_crossing_is_reported() -> None:
    history = [
        _pt("2026-06-10", 80.0, "B", 60),  # current
        _pt("2026-06-12", 79.0, "B", 20),  # expiring_soon
    ]
    events = history_events(history)
    assert len(events) == 1
    assert events[0].kind == "expiry"
    assert "expiry window" in events[0].detail and "20 days" in events[0].detail


def test_feed_expired_phrasing_when_grade_holds() -> None:
    # Same grade but the calendar lapsed, so the expiry branch fires.
    events = history_events([_pt("a", 60, "C", 5), _pt("b", 58, "C", -2)])
    assert events[0].kind == "expiry"
    assert events[0].detail == "Feed expired."


def test_grade_change_wins_over_expiry_when_both_move() -> None:
    renewed = history_events(
        [_pt("a", 0, "F", -5, freshness=0.0), _pt("b", 80, "B", 90, freshness=85.0)]
    )
    assert renewed[0].kind == "grade_change"


def test_score_move_without_grade_change() -> None:
    history = [
        _pt("2026-06-10", 84.0, "B", 80, completeness=60.0),
        _pt("2026-06-12", 88.0, "B", 79, completeness=70.0),
    ]
    events = history_events(history)
    assert events[0].kind == "score_move"
    assert "Score rose 4 points" in events[0].detail
    assert "rider experience rose 10 points" in events[0].detail


def test_steady_history_and_short_history_produce_no_events() -> None:
    steady = [_pt("a", 84.0, "B", 80), _pt("b", 84.5, "B", 79), _pt("c", 84.0, "B", 78)]
    assert history_events(steady) == []
    assert history_events([_pt("a", 84.0, "B", 80)]) == []
    assert history_events([]) == []
