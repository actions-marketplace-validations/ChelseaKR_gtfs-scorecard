"""Tests for the equity overlay (pure classifier + ACS parse + join)."""

from __future__ import annotations

from typing import Any

from scorecard_pipeline.equity import (
    HIGH,
    LOWER,
    MODERATE,
    UNKNOWN,
    EquityIndicators,
    build_overlay,
    need_tier,
    parse_acs,
    render_overlay,
)


def test_need_tier_bands() -> None:
    # Two indicators high -> high.
    assert need_tier(EquityIndicators(poverty_pct=20.0, zero_vehicle_pct=15.0)) == HIGH
    # One high -> moderate.
    assert need_tier(EquityIndicators(poverty_pct=20.0, zero_vehicle_pct=5.0)) == MODERATE
    # Data present, none high -> lower.
    assert need_tier(EquityIndicators(poverty_pct=8.0, disability_pct=10.0)) == LOWER
    # No data -> unknown.
    assert need_tier(EquityIndicators()) == UNKNOWN


def _rows() -> list[dict[str, Any]]:
    return [
        {"id": "a", "grade": "F", "score": 40.0},
        {"id": "b", "grade": "D", "score": 62.0},
        {"id": "c", "grade": "A", "score": 95.0},
        {"id": "d", "grade": "B", "score": 84.0},
        {"id": "e", "grade": "F", "score": 30.0},  # no state -> dropped
    ]


def test_build_overlay_joins_need_and_low_grade_share() -> None:
    states = {"a": "California", "b": "California", "c": "California", "d": "Vermont"}
    indicators = {
        "California": EquityIndicators(poverty_pct=20.0, zero_vehicle_pct=14.0),  # high
        "Vermont": EquityIndicators(poverty_pct=9.0, zero_vehicle_pct=6.0),  # lower
    }
    overlay = build_overlay(_rows(), states, indicators)
    by_state = {s["state"]: s for s in overlay["states"]}
    assert by_state["California"]["need_tier"] == HIGH
    assert by_state["California"]["agency_count"] == 3
    # a (F) and b (D) of 3 are low grade.
    assert by_state["California"]["low_grade_share"] == round(2 / 3 * 100, 1)
    assert by_state["Vermont"]["need_tier"] == LOWER
    # Priority lists only high-need states.
    assert [s["state"] for s in overlay["priority"]] == ["California"]
    # Agency 'e' had no state and is excluded.
    assert "e" not in {r for s in overlay["states"] for r in [s["state"]]}


def test_build_overlay_without_indicators_is_unknown_and_no_priority() -> None:
    overlay = build_overlay(_rows(), {"a": "California"}, {})
    assert overlay["states"][0]["need_tier"] == UNKNOWN
    assert overlay["priority"] == []


def test_parse_acs_combines_subject_and_detail_by_name() -> None:
    subject = [
        ["NAME", "S1701_C03_001E", "S1810_C03_001E", "state"],
        ["California", "20.5", "11.0", "06"],
        ["Vermont", "9.1", "16.0", "50"],
    ]
    # B08201: total households, then no-vehicle households.
    detail = [
        ["NAME", "B08201_001E", "B08201_002E", "state"],
        ["California", "1000", "132", "06"],  # 13.2%
        ["Vermont", "200", "10", "50"],  # 5.0%
    ]
    out = parse_acs(subject, detail)
    assert out["California"].poverty_pct == 20.5
    assert out["California"].zero_vehicle_pct == 13.2
    assert out["California"].disability_pct == 11.0
    assert out["Vermont"].zero_vehicle_pct == 5.0
    assert out["Vermont"].disability_pct == 16.0


def test_parse_acs_drops_suppressed_sentinels() -> None:
    subject = [
        ["NAME", "S1701_C03_001E", "S1810_C03_001E", "state"],
        ["Nowhere", "-666666666", "12.0", "99"],
    ]
    out = parse_acs(subject, [])
    assert out["Nowhere"].poverty_pct is None
    assert out["Nowhere"].disability_pct == 12.0


def test_render_overlay_lists_priority_states() -> None:
    states = {"a": "California", "b": "California"}
    indicators = {"California": EquityIndicators(poverty_pct=20.0, zero_vehicle_pct=14.0)}
    report = render_overlay(build_overlay(_rows(), states, indicators))
    assert "California" in report
    assert "high need" in report.lower()
