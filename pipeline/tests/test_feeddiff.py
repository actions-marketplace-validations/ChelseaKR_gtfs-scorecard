"""Tests for the snapshot-to-snapshot feed diff."""

from __future__ import annotations

from typing import Any

from scorecard_pipeline.feeddiff import diff_artifacts


def _artifact(
    *,
    date: str = "2026-06-12",
    grade: str = "B",
    score: float = 82.0,
    findings: list[dict[str, Any]] | None = None,
    sha256: str = "aaa",
    size_bytes: int = 1000,
    days_until_expiry: int | None = 90,
) -> dict[str, Any]:
    return {
        "snapshot_date": date,
        "overall": {"grade": grade, "score": score},
        "feed": {"sha256": sha256, "size_bytes": size_bytes},
        "categories": {
            "correctness": {
                "status": "measured",
                "score": 90.0,
                "findings": findings or [],
            },
            "freshness": {
                "status": "measured",
                "score": 80.0,
                "details": {"days_until_expiry": days_until_expiry},
                "findings": [],
            },
        },
    }


def _finding(code: str, count: int, severity: str = "WARNING", what: str = "") -> dict[str, Any]:
    return {"code": code, "count": count, "severity": severity, "what": what or f"{code} happened"}


def test_new_finding_is_detected() -> None:
    prev = _artifact(findings=[])
    curr = _artifact(findings=[_finding("stop_too_far", 3)])
    diff = diff_artifacts(prev, curr)
    assert [c.code for c in diff.new] == ["stop_too_far"]
    assert diff.new[0].curr_count == 3
    assert diff.new[0].prev_count is None
    assert not diff.resolved


def test_resolved_finding_is_detected() -> None:
    prev = _artifact(findings=[_finding("missing_headsign", 5)])
    curr = _artifact(findings=[])
    diff = diff_artifacts(prev, curr)
    assert [c.code for c in diff.resolved] == ["missing_headsign"]
    assert diff.resolved[0].prev_count == 5
    assert diff.resolved[0].curr_count is None
    assert not diff.new


def test_changed_count_is_detected() -> None:
    prev = _artifact(findings=[_finding("stop_too_far", 3)])
    curr = _artifact(findings=[_finding("stop_too_far", 8)])
    diff = diff_artifacts(prev, curr)
    assert not diff.new and not diff.resolved
    assert len(diff.changed) == 1
    assert (diff.changed[0].prev_count, diff.changed[0].curr_count) == (3, 8)


def test_unchanged_count_is_not_reported() -> None:
    f = [_finding("stop_too_far", 3)]
    diff = diff_artifacts(_artifact(findings=f), _artifact(findings=list(f)))
    assert not diff.changed and not diff.new and not diff.resolved


def test_feed_bytes_change_detected_from_sha() -> None:
    prev = _artifact(sha256="aaa", size_bytes=1000)
    curr = _artifact(sha256="bbb", size_bytes=2024)
    diff = diff_artifacts(prev, curr)
    assert diff.feed_bytes_changed is True
    assert diff.size_delta == 1024


def test_same_sha_is_not_a_feed_change() -> None:
    diff = diff_artifacts(_artifact(sha256="aaa"), _artifact(sha256="aaa"))
    assert diff.feed_bytes_changed is False


def test_grade_drop_and_score_delta() -> None:
    prev = _artifact(grade="B", score=82.0)
    curr = _artifact(grade="C", score=74.5)
    diff = diff_artifacts(prev, curr)
    assert diff.grade_moved is True
    assert diff.grade_dropped is True
    assert diff.score_delta == -7.5


def test_grade_rise_is_not_a_drop() -> None:
    diff = diff_artifacts(_artifact(grade="C", score=72.0), _artifact(grade="B", score=83.0))
    assert diff.grade_moved is True
    assert diff.grade_dropped is False
    assert diff.score_delta == 11.0


def test_expiry_delta() -> None:
    diff = diff_artifacts(_artifact(days_until_expiry=40), _artifact(days_until_expiry=10))
    assert diff.expiry_delta == -30


def test_identical_snapshots_have_no_changes() -> None:
    a = _artifact(findings=[_finding("x", 1)])
    diff = diff_artifacts(a, dict(a))
    assert diff.has_changes is False


def test_new_findings_sorted_by_severity() -> None:
    curr = _artifact(
        findings=[
            _finding("info_one", 100, severity="INFO"),
            _finding("err_one", 1, severity="ERROR"),
            _finding("warn_one", 2, severity="WARNING"),
        ]
    )
    diff = diff_artifacts(_artifact(findings=[]), curr)
    assert [c.code for c in diff.new] == ["err_one", "warn_one", "info_one"]


def test_unmeasured_category_findings_are_ignored() -> None:
    prev = _artifact(findings=[])
    curr = _artifact(findings=[])
    curr["categories"]["realtime"] = {
        "status": "not_yet_measured",
        "findings": [_finding("rt_problem", 9)],
    }
    diff = diff_artifacts(prev, curr)
    assert diff.new == []
