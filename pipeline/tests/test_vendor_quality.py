"""Tests for quality benchmarking by feed host (the export-tool proxy)."""

from __future__ import annotations

from scorecard_pipeline.vendors import (
    MIN_AGENCIES_FOR_BENCHMARK,
    VendorQuality,
    render_vendor_quality,
    vendor_quality,
)


def record(agency_id: str, host_url: str, grade: str, score: float) -> dict[str, object]:
    return {
        "id": agency_id,
        "feed_url": host_url,
        "grade": grade,
        "score": score,
        "stops": 100,
    }


def test_min_agencies_constant_is_two() -> None:
    assert MIN_AGENCIES_FOR_BENCHMARK == 2


def test_empty_input_returns_empty() -> None:
    assert vendor_quality([]) == []


def test_groups_average_median_and_distribution() -> None:
    records = [
        record("a", "http://data.trilliumtransit.com/a.zip", "B", 80.0),
        record("b", "http://data.trilliumtransit.com/b.zip", "B", 90.0),
        record("c", "http://data.trilliumtransit.com/c.zip", "D", 60.0),
        record("d", "https://avl.example.org/d.zip", "A", 95.0),
        record("e", "https://avl.example.org/e.zip", "C", 75.0),
    ]
    stats = vendor_quality(records)

    # Two qualifying hosts; Trillium first (more agencies), then example.org.
    assert [s.host for s in stats] == ["data.trilliumtransit.com", "avl.example.org"]

    trillium = stats[0]
    assert trillium.agency_count == 3
    # mean(80, 90, 60) = 76.6667 -> 76.7
    assert trillium.avg_score == 76.7
    # median(60, 80, 90) = 80
    assert trillium.median_score == 80.0
    assert trillium.grade_distribution == {"B": 2, "D": 1}

    other = stats[1]
    assert other.agency_count == 2
    assert other.avg_score == 85.0
    assert other.median_score == 85.0
    assert other.grade_distribution == {"A": 1, "C": 1}


def test_single_agency_host_excluded() -> None:
    records = [
        record("a", "http://data.trilliumtransit.com/a.zip", "B", 80.0),
        record("b", "http://data.trilliumtransit.com/b.zip", "C", 70.0),
        record("solo", "https://lonely.example.net/g.zip", "A", 99.0),
    ]
    stats = vendor_quality(records)
    assert [s.host for s in stats] == ["data.trilliumtransit.com"]
    assert all(s.host != "lonely.example.net" for s in stats)


def test_sort_breaks_ties_by_host_name() -> None:
    records = [
        record("a", "https://zeta.example.com/a.zip", "B", 80.0),
        record("b", "https://zeta.example.com/b.zip", "B", 80.0),
        record("c", "https://alpha.example.com/c.zip", "B", 80.0),
        record("d", "https://alpha.example.com/d.zip", "B", 80.0),
    ]
    stats = vendor_quality(records)
    # Equal agency counts: alpha sorts before zeta.
    assert [s.host for s in stats] == ["alpha.example.com", "zeta.example.com"]


def test_render_includes_table_and_fairness_note() -> None:
    stats = [
        VendorQuality(
            host="data.trilliumtransit.com",
            agency_count=3,
            avg_score=76.7,
            grade_distribution={"B": 2, "D": 1},
            median_score=80.0,
        )
    ]
    out = render_vendor_quality(stats)
    assert "data.trilliumtransit.com" in out
    assert "| Host |" in out
    assert "B: 2" in out
    assert "not adjusted for" in out
    assert "rank" not in out.lower()


def test_render_handles_empty_stats() -> None:
    out = render_vendor_quality([])
    assert "enough agencies to benchmark" in out
