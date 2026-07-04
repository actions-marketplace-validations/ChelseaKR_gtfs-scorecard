"""Tests against a trimmed copy of the real Unitrans feed.

The fixture is the 2026-06-11 Unitrans GTFS snapshot with large files cut to
their first rows; feed_info, agency, and the calendars are kept whole. It
guards the readers against real-world quirks (BOM, vendor extra files like
rider_categories.txt) that synthetic fixtures don't reproduce.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from scorecard_pipeline.gtfs import read_feed_dates
from scorecard_pipeline.metrics import freshness

FIXTURE = Path(__file__).parent / "fixtures" / "unitrans_trimmed.zip"


def test_reads_real_feed_dates() -> None:
    dates = read_feed_dates(str(FIXTURE))
    assert dates.has_feed_info
    assert dates.feed_publisher_name == "Unitrans"
    assert dates.feed_version == "Spring-SS12026_V1"
    assert dates.feed_start_date == dt.date(2026, 4, 22)
    assert dates.feed_end_date == dt.date(2026, 8, 2)
    assert dates.last_service_date == dt.date(2026, 8, 2)
    assert dates.effective_expiry() == dt.date(2026, 8, 2)


def test_freshness_on_real_feed_as_of_snapshot_day() -> None:
    result = freshness(read_feed_dates(str(FIXTURE)), today=dt.date(2026, 6, 11))
    # 52 days of runway on the snapshot date: solid but not full credit
    assert result.details["days_until_expiry"] == 52
    assert 80.0 < result.score < 100.0
