"""Tests for fix receipts: dated, durable records of cleared findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scorecard_pipeline.fixlog import (
    diff_receipts,
    finding_codes,
    load_fixlog,
    merge_receipts,
)


def _artifact(date: str, *codes: tuple[str, str], measured: bool = True) -> dict[str, Any]:
    return {
        "snapshot_date": date,
        "categories": {
            "correctness": {
                "status": "measured" if measured else "skipped",
                "findings": [{"code": c, "what": w} for c, w in codes],
            }
        },
    }


def test_receipt_records_both_dates_and_prior_wording() -> None:
    prev = _artifact("2026-06-30", ("expired_calendar", "3 calendars expired."))
    cur = _artifact("2026-07-01")
    receipts = diff_receipts(prev, cur)
    assert receipts == [
        {
            "code": "expired_calendar",
            "what": "3 calendars expired.",
            "last_seen": "2026-06-30",
            "cleared": "2026-07-01",
        }
    ]


def test_no_receipt_without_previous_artifact_or_when_still_present() -> None:
    cur = _artifact("2026-07-01", ("x", "still here"))
    assert diff_receipts(None, cur) == []
    prev = _artifact("2026-06-30", ("x", "still here"))
    assert diff_receipts(prev, cur) == []


def test_unmeasured_category_never_yields_a_receipt() -> None:
    # A category that went unmeasured (fetch failed, RT down) must not read as
    # "everything in it was fixed". The finding is invisible today, not fixed,
    # and this is a permanent record.
    prev = _artifact("2026-06-30", ("x", "w"))
    cur = _artifact("2026-07-01", measured=False)
    assert finding_codes(prev) == {"x": "w"}
    assert finding_codes(cur) == {}
    assert diff_receipts(prev, cur) == []


def test_merge_is_idempotent_and_keeps_history() -> None:
    old = [{"code": "a", "what": "w1", "last_seen": "2026-06-01", "cleared": "2026-06-02"}]
    new = [
        {"code": "a", "what": "w1", "last_seen": "2026-06-01", "cleared": "2026-06-02"},
        {"code": "a", "what": "w1 again", "last_seen": "2026-06-10", "cleared": "2026-06-11"},
    ]
    merged = merge_receipts(old, new)
    # Same (cleared, code) dedupes; a later re-clear of the same code is distinct.
    assert len(merged) == 2
    assert merge_receipts(merged, new) == merged
    # Oldest first, so the log reads as a history.
    assert merged[0]["cleared"] == "2026-06-02"


def test_merge_keeps_receipts_whose_dated_artifacts_are_gone() -> None:
    # The durable property: a receipt already in the file survives even when
    # the walk over dated artifacts no longer produces it.
    old = [{"code": "gone", "what": "w", "last_seen": "2025-01-01", "cleared": "2025-01-02"}]
    assert merge_receipts(old, []) == old


def test_load_fixlog_missing_or_bad_file(tmp_path: Path) -> None:
    assert load_fixlog(tmp_path) == []
    (tmp_path / "fixlog.json").write_text("not json")
    assert load_fixlog(tmp_path) == []
    (tmp_path / "fixlog.json").write_text(json.dumps({"receipts": [{"code": "a"}, "junk"]}))
    assert load_fixlog(tmp_path) == [{"code": "a"}]
