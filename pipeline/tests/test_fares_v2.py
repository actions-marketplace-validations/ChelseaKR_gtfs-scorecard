"""Tests for Fares v2 awareness: rider categories, fare media, and contactless EMV.

These exercise the pure logic directly with fabricated profiles and rows, plus a
couple of end-to-end checks that read a built zip, so the detection and the
opportunity findings stay in step (ADR 0008: zero-deduction, framed as fixes).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from scorecard_pipeline.fares import (
    FARE_MEDIA_TYPE_CONTACTLESS_EMV,
    FaresV2Profile,
    _has_contactless_emv,
    detect_fares_v2,
    fares_v2_findings,
    fares_v2_findings_for,
)

BASE = {
    "agency.txt": "agency_id,agency_name\nx,X\n",
    "stops.txt": "stop_id,stop_name\nS1,Main St\n",
    "trips.txt": "route_id,service_id,trip_id\nR1,WK,T1\n",
}
PRODUCTS = "fare_product_id,fare_product_name,amount,currency\np1,Single,2.50,USD\n"


# --- pure findings logic ------------------------------------------------------


def test_no_products_yields_no_v2_findings() -> None:
    """A fare-free or no-fares feed stays neutral here."""
    profile = FaresV2Profile(
        has_products=False,
        has_rider_categories=False,
        has_fare_media=False,
        has_contactless_emv=False,
    )
    assert fares_v2_findings_for(profile) == []


def test_products_without_rider_categories_is_flagged() -> None:
    profile = FaresV2Profile(
        has_products=True,
        has_rider_categories=False,
        has_fare_media=True,
        has_contactless_emv=True,
    )
    codes = [f.code for f in fares_v2_findings_for(profile)]
    assert codes == ["scorecard_fares_v2_no_rider_categories"]


def test_products_without_fare_media_is_flagged() -> None:
    profile = FaresV2Profile(
        has_products=True,
        has_rider_categories=True,
        has_fare_media=False,
        has_contactless_emv=False,
    )
    findings = fares_v2_findings_for(profile)
    assert [f.code for f in findings] == ["scorecard_fares_v2_no_fare_media"]
    assert all(f.deduction == 0.0 for f in findings)


def test_complete_v2_payment_metadata_yields_nothing() -> None:
    profile = FaresV2Profile(
        has_products=True,
        has_rider_categories=True,
        has_fare_media=True,
        has_contactless_emv=True,
    )
    assert fares_v2_findings_for(profile) == []


def test_products_with_neither_flags_both() -> None:
    profile = FaresV2Profile(
        has_products=True,
        has_rider_categories=False,
        has_fare_media=False,
        has_contactless_emv=False,
    )
    codes = {f.code for f in fares_v2_findings_for(profile)}
    assert codes == {
        "scorecard_fares_v2_no_rider_categories",
        "scorecard_fares_v2_no_fare_media",
    }


# --- contactless EMV detection ------------------------------------------------


def test_contactless_emv_detected_when_flagged() -> None:
    rows = [
        {"fare_media_id": "card", "fare_media_type": "2"},
        {"fare_media_id": "tap", "fare_media_type": FARE_MEDIA_TYPE_CONTACTLESS_EMV},
    ]
    assert _has_contactless_emv(rows) is True


def test_contactless_emv_absent_without_the_type() -> None:
    rows = [
        {"fare_media_id": "cash", "fare_media_type": "0"},
        {"fare_media_id": "card", "fare_media_type": "2"},
    ]
    assert _has_contactless_emv(rows) is False


def test_contactless_emv_tolerates_whitespace_and_missing_field() -> None:
    assert _has_contactless_emv([{"fare_media_type": " 4 "}]) is True
    assert _has_contactless_emv([{"fare_media_id": "only"}]) is False
    assert _has_contactless_emv([]) is False


# --- end to end through a built zip -------------------------------------------


def test_detect_reads_all_three_signals(make_gtfs_zip: Callable[..., Path]) -> None:
    feed = {
        **BASE,
        "fare_products.txt": PRODUCTS,
        "rider_categories.txt": "rider_category_id,rider_category_name\nsenior,Senior\n",
        "fare_media.txt": "fare_media_id,fare_media_name,fare_media_type\ntap,Tap to pay,4\n",
    }
    profile = detect_fares_v2(str(make_gtfs_zip(feed)))
    assert profile.has_products is True
    assert profile.has_rider_categories is True
    assert profile.has_fare_media is True
    assert profile.has_contactless_emv is True
    assert fares_v2_findings(str(make_gtfs_zip(feed))) == []


def test_no_fares_feed_produces_no_v2_findings(make_gtfs_zip: Callable[..., Path]) -> None:
    profile = detect_fares_v2(str(make_gtfs_zip(BASE)))
    assert profile.has_products is False
    assert fares_v2_findings(str(make_gtfs_zip(BASE))) == []


def test_products_only_flags_both_through_zip(make_gtfs_zip: Callable[..., Path]) -> None:
    feed = {**BASE, "fare_products.txt": PRODUCTS}
    findings = fares_v2_findings(str(make_gtfs_zip(feed)))
    assert {f.code for f in findings} == {
        "scorecard_fares_v2_no_rider_categories",
        "scorecard_fares_v2_no_fare_media",
    }
