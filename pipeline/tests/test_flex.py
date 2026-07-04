"""Tests for GTFS-Flex detection and booking-reachability (ADR 0007)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from scorecard_pipeline.flex import detect_flex, flex_findings

BARE = {
    "agency.txt": "agency_id,agency_name\nx,X\n",
    "stops.txt": "stop_id,stop_name\nS1,Main St\n",
    "trips.txt": "route_id,service_id,trip_id\nR1,WK,T1\n",
}


def test_plain_fixed_feed_is_not_flex(make_gtfs_zip: Callable[..., Path]) -> None:
    profile = detect_flex(str(make_gtfs_zip(BARE)))
    assert profile.has_flex is False
    assert flex_findings(profile) == []


def test_flex_with_reachable_booking_is_acknowledged(
    make_gtfs_zip: Callable[..., Path],
) -> None:
    feed = {
        **BARE,
        "locations.geojson": '{"type":"FeatureCollection","features":[]}',
        "booking_rules.txt": "booking_rule_id,booking_type,phone_number\nBR1,1,530-555-0100\n",
    }
    profile = detect_flex(str(make_gtfs_zip(feed)))
    assert profile.has_flex is True
    assert profile.booking_reachable is True
    (note,) = flex_findings(profile)
    assert note.code == "scorecard_flex_service"
    assert note.severity == "INFO"
    assert note.deduction == 0.0  # no grade change in this slice


def test_real_time_booking_counts_as_reachable(make_gtfs_zip: Callable[..., Path]) -> None:
    feed = {
        **BARE,
        "booking_rules.txt": "booking_rule_id,booking_type\nBR1,0\n",
    }
    profile = detect_flex(str(make_gtfs_zip(feed)))
    assert profile.has_flex is True
    assert profile.booking_reachable is True


def test_flex_without_booking_rules_is_flagged(make_gtfs_zip: Callable[..., Path]) -> None:
    feed = {**BARE, "locations.geojson": '{"type":"FeatureCollection","features":[]}'}
    profile = detect_flex(str(make_gtfs_zip(feed)))
    assert profile.has_flex is True
    assert profile.has_booking_rules is False
    (finding,) = flex_findings(profile)
    assert finding.code == "scorecard_flex_no_booking_rules"
    assert finding.deduction == 0.0


def test_flex_booking_without_contact_is_flagged(make_gtfs_zip: Callable[..., Path]) -> None:
    feed = {
        **BARE,
        "booking_rules.txt": "booking_rule_id,booking_type,prior_notice_duration_min\nBR1,1,1440\n",
    }
    profile = detect_flex(str(make_gtfs_zip(feed)))
    assert profile.has_flex is True
    assert profile.booking_reachable is False
    (finding,) = flex_findings(profile)
    assert finding.code == "scorecard_flex_booking_unreachable"
    assert finding.deduction == 0.0
