"""Tests for per-agency map geometry (pure)."""

from __future__ import annotations

from scorecard_pipeline.geo import agency_geo_from_stops


def _stops(*coords: tuple[str, str]) -> list[dict[str, str]]:
    return [{"stop_lat": lat, "stop_lon": lon} for lat, lon in coords]


def test_point_is_the_per_axis_median() -> None:
    geo = agency_geo_from_stops(_stops(("38.5", "-121.7"), ("38.6", "-121.8"), ("38.7", "-121.9")))
    assert geo is not None
    assert geo.lat == 38.6
    assert geo.lon == -121.8
    assert geo.stop_count == 3


def test_bbox_spans_the_extremes() -> None:
    geo = agency_geo_from_stops(_stops(("38.5", "-121.9"), ("38.7", "-121.7")))
    assert geo is not None
    assert geo.bbox == (-121.9, 38.5, -121.7, 38.7)


def test_median_outlier_does_not_drag_the_point_off_the_service_area() -> None:
    # A depot far north should not move the representative point much.
    geo = agency_geo_from_stops(
        _stops(("38.5", "-121.7"), ("38.5", "-121.7"), ("38.5", "-121.7"), ("60.0", "-150.0"))
    )
    assert geo is not None
    assert geo.lat == 38.5
    assert geo.lon == -121.7


def test_blank_and_null_island_and_out_of_range_rows_are_skipped() -> None:
    geo = agency_geo_from_stops(
        _stops(
            ("", ""),  # blank
            ("0", "0"),  # null island
            ("200", "-50"),  # out of range latitude
            ("38.5", "-121.7"),  # the only real one
        )
    )
    assert geo is not None
    assert geo.stop_count == 1
    assert (geo.lat, geo.lon) == (38.5, -121.7)


def test_no_located_stops_returns_none() -> None:
    assert agency_geo_from_stops(_stops(("", ""), ("0", "0"))) is None
    assert agency_geo_from_stops([]) is None


def test_to_dict_rounds_and_shapes_for_json() -> None:
    geo = agency_geo_from_stops(_stops(("38.123456", "-121.987654")))
    assert geo is not None
    d = geo.to_dict()
    assert d == {
        "lon": -121.98765,
        "lat": 38.12346,
        "bbox": [-121.98765, 38.12346, -121.98765, 38.12346],
        "stop_count": 1,
    }
