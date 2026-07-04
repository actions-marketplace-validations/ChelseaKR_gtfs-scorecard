"""Tests for the tract-level equity geospatial core (pure)."""

from __future__ import annotations

from scorecard_pipeline.equity import HIGH, LOWER, EquityIndicators
from scorecard_pipeline.tract_equity import (
    Tract,
    locate,
    point_in_polygon,
    served_area_indicators,
    served_area_need,
)

# A unit square from (0,0) to (1,1), and a second from (1,0) to (2,1).
_SQUARE_A = [[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]]
_SQUARE_B = [[(1.0, 0.0), (2.0, 0.0), (2.0, 1.0), (1.0, 1.0), (1.0, 0.0)]]

# A square with a hole in the middle (0.4-0.6).
_HOLED = [
    [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)],
    [(0.4, 0.4), (0.6, 0.4), (0.6, 0.6), (0.4, 0.6), (0.4, 0.4)],
]


def test_point_in_polygon_basic() -> None:
    assert point_in_polygon(0.5, 0.5, _SQUARE_A) is True
    assert point_in_polygon(1.5, 0.5, _SQUARE_A) is False


def test_point_in_polygon_respects_holes() -> None:
    assert point_in_polygon(0.5, 0.5, _HOLED) is False  # in the hole
    assert point_in_polygon(0.1, 0.1, _HOLED) is True  # in the ring, outside the hole


def _tracts() -> list[Tract]:
    return [
        Tract("A", _SQUARE_A, EquityIndicators(poverty_pct=25.0, zero_vehicle_pct=20.0)),
        Tract("B", _SQUARE_B, EquityIndicators(poverty_pct=5.0, zero_vehicle_pct=2.0)),
    ]


def test_locate_finds_the_containing_tract() -> None:
    tracts = _tracts()
    a = locate(0.5, 0.5, tracts)
    b = locate(1.5, 0.5, tracts)
    assert a is not None and a.geoid == "A"
    assert b is not None and b.geoid == "B"
    assert locate(9.0, 9.0, tracts) is None


def test_served_area_indicators_are_stop_weighted() -> None:
    # Three stops in A (high need), one in B (low need): the mean leans high.
    stops = [(0.5, 0.5), (0.2, 0.2), (0.8, 0.8), (1.5, 0.5)]
    ind = served_area_indicators(stops, _tracts())
    # poverty: (25*3 + 5*1)/4 = 20.0; zero_vehicle: (20*3 + 2*1)/4 = 15.5
    assert ind.poverty_pct == 20.0
    assert ind.zero_vehicle_pct == 15.5


def test_served_area_need_tier() -> None:
    stops = [(0.5, 0.5), (0.2, 0.2), (0.8, 0.8)]  # all in high-need tract A
    tier, ind = served_area_need(stops, _tracts())
    assert tier == HIGH
    assert ind.poverty_pct == 25.0


def test_stops_outside_all_tracts_are_skipped() -> None:
    stops = [(0.5, 0.5), (9.0, 9.0)]  # second stop is nowhere
    ind = served_area_indicators(stops, _tracts())
    assert ind.poverty_pct == 25.0  # only the located stop counts


def test_no_located_stops_yields_lower_or_unknown() -> None:
    tier, ind = served_area_need([(9.0, 9.0)], _tracts())
    assert ind.poverty_pct is None
    assert tier in (LOWER, "unknown")
