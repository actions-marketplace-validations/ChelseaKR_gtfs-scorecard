"""Tests for fare-model classification and the published-not-applied gap (ADR 0008)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from scorecard_pipeline.fares import detect_fares, fares_findings

BASE = {
    "agency.txt": "agency_id,agency_name\nx,X\n",
    "stops.txt": "stop_id,stop_name\nS1,Main St\n",
    "trips.txt": "route_id,service_id,trip_id\nR1,WK,T1\n",
}


def test_no_fares(make_gtfs_zip: Callable[..., Path]) -> None:
    profile = detect_fares(str(make_gtfs_zip(BASE)))
    assert profile.model == "none"
    assert profile.applied is False
    assert fares_findings(profile) == []


def test_legacy_fares_are_applied(make_gtfs_zip: Callable[..., Path]) -> None:
    feed = {**BASE, "fare_attributes.txt": "fare_id,price,currency_type\nbase,2.25,USD\n"}
    profile = detect_fares(str(make_gtfs_zip(feed)))
    assert profile.model == "legacy"
    assert profile.applied is True
    assert fares_findings(profile) == []


def test_v2_with_leg_rules_is_applied(make_gtfs_zip: Callable[..., Path]) -> None:
    feed = {
        **BASE,
        "fare_products.txt": "fare_product_id,fare_product_name,amount,currency\n"
        "p1,Single,2.50,USD\n",
        "fare_leg_rules.txt": "leg_group_id,network_id,fare_product_id\nlg1,,p1\n",
    }
    profile = detect_fares(str(make_gtfs_zip(feed)))
    assert profile.model == "v2"
    assert profile.applied is True
    assert fares_findings(profile) == []


def test_v2_products_without_leg_rules_is_flagged(make_gtfs_zip: Callable[..., Path]) -> None:
    feed = {
        **BASE,
        "fare_products.txt": "fare_product_id,fare_product_name,amount,currency\n"
        "p1,Single,2.50,USD\np2,Day,5.00,USD\n",
    }
    profile = detect_fares(str(make_gtfs_zip(feed)))
    assert profile.model == "v2"
    assert profile.has_leg_rules is False
    assert profile.applied is False
    (finding,) = fares_findings(profile)
    assert finding.code == "scorecard_fares_published_not_applied"
    assert finding.count == 2
    assert finding.deduction == 0.0  # no grade change in this slice
