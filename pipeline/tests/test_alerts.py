"""Tests for the expiry/regression alert digest."""

from __future__ import annotations

import datetime as dt
import json

from scorecard_pipeline.alerts import build_digest, render_digest
from scorecard_pipeline.config import artifacts_dir


def write_latest(
    agency_id: str, name: str, score: float, grade: str, days_until_expiry: int | None
) -> None:
    path = artifacts_dir() / agency_id
    path.mkdir(parents=True, exist_ok=True)
    (path / "latest.json").write_text(
        json.dumps(
            {
                "agency": {"id": agency_id, "name": name},
                "snapshot_date": "2026-06-12",
                "overall": {"score": score, "grade": grade},
                "categories": {
                    "freshness": {"details": {"days_until_expiry": days_until_expiry}},
                },
                "top_fixes": [],
            }
        )
    )


def write_index(entries: dict[str, dict]) -> None:  # type: ignore[type-arg]
    path = artifacts_dir() / "index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": "1.1", "agencies": entries}))


def test_flags_feed_expiring_within_window() -> None:
    write_latest("soon", "Soon Transit", 90.0, "A", days_until_expiry=10)
    write_index(
        {
            "soon": {
                "name": "Soon Transit",
                "history": [
                    {"date": "2026-06-12", "score": 90.0, "grade": "A"},
                ],
            }
        }
    )
    digest = build_digest(today=dt.date(2026, 6, 12), expiry_days=21)
    kinds = {(i.agency_id, i.kind) for i in digest.items}
    assert ("soon", "expiry") in kinds


def test_healthy_feed_produces_no_items() -> None:
    write_latest("ok", "OK Transit", 90.0, "A", days_until_expiry=120)
    write_index(
        {
            "ok": {
                "name": "OK Transit",
                "history": [
                    {"date": "2026-06-11", "score": 90.0, "grade": "A"},
                    {"date": "2026-06-12", "score": 90.0, "grade": "A"},
                ],
            }
        }
    )
    digest = build_digest(today=dt.date(2026, 6, 12))
    assert digest.items == []
    assert "No feeds need attention" in render_digest(digest)


def test_grade_drop_is_a_regression() -> None:
    write_latest("slip", "Slip Transit", 78.0, "C", days_until_expiry=200)
    write_index(
        {
            "slip": {
                "name": "Slip Transit",
                "history": [
                    {"date": "2026-06-11", "score": 84.0, "grade": "B"},
                    {"date": "2026-06-12", "score": 78.0, "grade": "C"},
                ],
            }
        }
    )
    digest = build_digest(today=dt.date(2026, 6, 12))
    regressions = [i for i in digest.items if i.kind == "regression"]
    assert regressions and regressions[0].agency_id == "slip"


def test_small_wobble_is_not_a_regression() -> None:
    write_latest("steady", "Steady Transit", 83.0, "B", days_until_expiry=200)
    write_index(
        {
            "steady": {
                "name": "Steady Transit",
                "history": [
                    {"date": "2026-06-11", "score": 84.0, "grade": "B"},
                    {"date": "2026-06-12", "score": 83.0, "grade": "B"},
                ],
            }
        }
    )
    digest = build_digest(today=dt.date(2026, 6, 12))
    assert [i for i in digest.items if i.kind == "regression"] == []


def test_render_includes_fix_language() -> None:
    write_latest("soon", "Soon Transit", 90.0, "A", days_until_expiry=3)
    write_index({"soon": {"name": "Soon Transit", "history": []}})
    text = render_digest(build_digest(today=dt.date(2026, 6, 12)))
    assert "Fix:" in text
    assert "Soon Transit" in text


def test_expiry_item_links_to_the_send_note_block() -> None:
    write_latest("soon", "Soon Transit", 90.0, "A", days_until_expiry=5)
    write_index({"soon": {"name": "Soon Transit", "history": []}})
    digest = build_digest(today=dt.date(2026, 6, 12))
    (item,) = [i for i in digest.items if i.kind == "expiry"]
    assert item.scorecard_url == "https://gtfsscorecard.org/agency/soon/#send-note"
    text = render_digest(digest)
    assert "Copy a note to send the agency" in text
    assert "https://gtfsscorecard.org/agency/soon/#send-note" in text


def test_sixty_day_feed_gets_a_first_heads_up() -> None:
    # Default window is now 60 days, so a feed two months out is flagged early.
    write_latest("ramp", "Ramp Transit", 90.0, "A", days_until_expiry=58)
    write_index({"ramp": {"name": "Ramp Transit", "history": []}})
    digest = build_digest(today=dt.date(2026, 6, 12))
    (item,) = [i for i in digest.items if i.kind == "expiry"]
    assert item.days_until_expiry == 58


def test_expiring_feeds_grouped_by_lead_time_tier() -> None:
    write_latest("week", "Week Transit", 90.0, "A", days_until_expiry=5)
    write_latest("month", "Month Transit", 90.0, "A", days_until_expiry=25)
    write_latest("dead", "Dead Transit", 40.0, "F", days_until_expiry=-3)
    write_index(
        {
            "week": {"name": "Week Transit", "history": []},
            "month": {"name": "Month Transit", "history": []},
            "dead": {"name": "Dead Transit", "history": []},
        }
    )
    digest = build_digest(today=dt.date(2026, 6, 12))
    # Soonest (most overdue) first.
    expiry_ids = [i.agency_id for i in digest.items if i.kind == "expiry"]
    assert expiry_ids == ["dead", "week", "month"]

    text = render_digest(digest)
    assert "Already expired" in text
    assert "Expires within a week" in text
    assert "Expires within a month" in text
    # the expired tier heading precedes the week tier heading in the output
    assert text.index("Already expired") < text.index("Expires within a week")
