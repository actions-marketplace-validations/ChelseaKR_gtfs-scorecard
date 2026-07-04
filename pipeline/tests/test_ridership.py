"""Tests for ridership-weighted impact (ridership.py)."""

from __future__ import annotations

from scorecard_pipeline.ridership import parse_ridership_csv, weighted_impact


def test_parse_finds_columns_by_header_and_sums_per_id() -> None:
    csv_text = (
        "Agency,NTD ID,Mode,UPT\n"
        "Alpha,90001,MB,1000\n"
        "Alpha,90001,DR,500\n"  # same reporter, second mode -> summed
        "Beta,90002,MB,2000\n"
    )
    rides = parse_ridership_csv(csv_text)
    assert rides == {"90001": 1500, "90002": 2000}


def test_parse_handles_commas_decimals_and_padding() -> None:
    csv_text = 'NTD ID,Unlinked Passenger Trips\n"0090001","1,234.0"\n90002,abc\n'
    rides = parse_ridership_csv(csv_text)
    # Thousands separator and decimal parsed; non-numeric row skipped; id digits kept.
    assert rides == {"90001": 1234}


def test_parse_returns_empty_when_columns_absent() -> None:
    assert parse_ridership_csv("Agency,State\nAlpha,CA\n") == {}
    assert parse_ridership_csv("") == {}


def test_weighted_impact_math() -> None:
    records = [
        {"ntd_id": "90001", "score": 90.0, "grade": "A", "expiry_status": "current"},
        {"ntd_id": "90002", "score": 50.0, "grade": "F", "expiry_status": "lapsed"},
        {"ntd_id": "99999", "score": 70.0, "grade": "C", "expiry_status": "current"},  # no rides
        {"ntd_id": "", "score": 80.0, "grade": "B", "expiry_status": "current"},  # no NTD id
    ]
    ridership = {"90001": 1_000_000, "90002": 100_000}
    imp = weighted_impact(records, ridership)
    assert imp["matched_agencies"] == 2
    assert imp["total_agencies"] == 4
    assert imp["total_annual_trips"] == 1_100_000
    # Only the lapsed feed's trips count as expired.
    assert imp["trips_on_expired_feeds"] == 100_000
    assert imp["expired_trips_pct"] == 9.1
    # Weighted by trips: (90*1e6 + 50*1e5) / 1.1e6 = 86.4
    assert imp["weighted_average_score"] == 86.4
    assert imp["trips_by_grade"]["A"] == 1_000_000
    assert imp["trips_by_grade"]["F"] == 100_000


def test_weighted_impact_empty_when_no_matches() -> None:
    records = [{"ntd_id": "90001", "score": 90.0, "grade": "A", "expiry_status": "current"}]
    imp = weighted_impact(records, {})  # no ridership data committed yet
    assert imp["matched_agencies"] == 0
    assert imp["total_annual_trips"] == 0
    assert imp["weighted_average_score"] is None
    assert imp["expired_trips_pct"] == 0.0
