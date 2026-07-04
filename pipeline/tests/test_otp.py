"""Tests for the OpenTripPlanner routing-QA glue (pure)."""

from __future__ import annotations

from scorecard_pipeline.otp import (
    PlanResult,
    assess_routing,
    parse_plan,
    plan_url,
    sample_od_pairs,
)


def test_sample_od_pairs_spans_the_area_deterministically() -> None:
    points = [(-121.9, 38.5), (-121.5, 38.7), (-121.7, 38.6), (-121.8, 38.55)]
    pairs = sample_od_pairs(points, count=2)
    assert len(pairs) == 2
    # First pair joins the longitudinal extremes; deterministic across runs.
    assert pairs[0] == ((-121.9, 38.5), (-121.5, 38.7))
    assert sample_od_pairs(points, count=2) == pairs


def test_sample_od_pairs_needs_two_distinct_points() -> None:
    assert sample_od_pairs([(1.0, 2.0)]) == []
    assert sample_od_pairs([(1.0, 2.0), (1.0, 2.0)]) == []


def test_plan_url_uses_lat_lon_order_and_anchors_time() -> None:
    url = plan_url(
        "http://otp:8080/", (-121.7, 38.5), (-121.5, 38.7), date="2026-06-21", time="08:00"
    )
    assert "/otp/routers/default/plan?" in url
    assert "fromPlace=38.5%2C-121.7" in url  # lat,lon
    assert "toPlace=38.7%2C-121.5" in url
    assert "date=2026-06-21" in url and "time=08%3A00" in url


def test_parse_plan_finds_itineraries() -> None:
    result = parse_plan({"plan": {"itineraries": [{"duration": 1200}, {"duration": 1500}]}})
    assert result.routable is True
    assert result.itinerary_count == 2


def test_parse_plan_handles_no_itineraries_and_errors() -> None:
    assert parse_plan({"plan": {"itineraries": []}}).routable is False
    err = parse_plan({"error": {"id": 404, "msg": "PATH_NOT_FOUND"}})
    assert err.routable is False
    assert err.error == "PATH_NOT_FOUND"


def test_assess_routing_verdict() -> None:
    qa = assess_routing(
        [
            PlanResult(routable=True, itinerary_count=1),
            PlanResult(routable=False, itinerary_count=0, error="PATH_NOT_FOUND"),
            PlanResult(routable=True, itinerary_count=2),
        ]
    )
    assert qa.pairs_tested == 3
    assert qa.pairs_routable == 2
    assert qa.all_routable is False
    assert round(qa.routable_share, 2) == 0.67
    assert qa.failures == ["PATH_NOT_FOUND"]


def test_assess_routing_all_pass() -> None:
    qa = assess_routing([PlanResult(routable=True, itinerary_count=1)])
    assert qa.all_routable is True
    assert qa.failures == []
