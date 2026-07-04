"""Tests for the beyond-the-grade recommendations aggregator."""

from __future__ import annotations

from pathlib import Path

from scorecard_pipeline.metrics import Finding
from scorecard_pipeline.recommend import _safe, gather_recommendations

FIXTURE = Path(__file__).parent / "fixtures" / "unitrans_trimmed.zip"


def test_gather_returns_serialized_findings_over_a_real_feed() -> None:
    recs = gather_recommendations(str(FIXTURE))
    assert isinstance(recs, list)
    # Whatever the fixture yields, every item is a serialized finding dict.
    for rec in recs:
        assert "code" in rec and "what" in rec and "fix" in rec


def test_a_failing_check_is_skipped_not_fatal() -> None:
    def boom() -> list[Finding]:
        raise RuntimeError("nope")

    assert _safe("x", boom) == []


def test_gather_on_a_missing_file_is_empty_not_an_error() -> None:
    # Each check sandboxes its own failure, so a bad path yields no recs, no raise.
    assert gather_recommendations("/no/such/feed.zip") == []
