"""Snapshot-to-snapshot diff of a feed's quality (the "what changed" view).

The pipeline keeps a dated artifact per agency per day. The trend chart shows the
shape of the score over time; this answers the next question a manager asks:
"what actually changed in my feed between the last two checks?" It compares two
artifacts and reports the change at the level a reader can act on — findings that
newly appeared, findings that cleared, findings whose instance count moved, and
whether the feed file itself was re-published — plus the overall grade, score, and
expiry-window movement.

True GTFS row-level diffing (which stop or route changed) needs the raw feed,
which the project does not archive. This works entirely from the published
artifacts on hand, so it is pure and reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Letter grades worst-to-best, for deciding whether a grade move is a drop.
_GRADE_ORDER = ["F", "D", "C", "B", "A"]
_MEASURED_CATEGORIES = ("correctness", "freshness", "completeness", "realtime")


@dataclass(frozen=True)
class FindingChange:
    """A single finding that appeared, cleared, or changed in instance count."""

    code: str
    what: str
    severity: str
    prev_count: int | None  # None when the finding is newly appeared
    curr_count: int | None  # None when the finding cleared


@dataclass
class FeedDiff:
    """The change between two snapshots of one feed, finding-level and overall."""

    prev_date: str
    curr_date: str
    new: list[FindingChange] = field(default_factory=list)
    resolved: list[FindingChange] = field(default_factory=list)
    changed: list[FindingChange] = field(default_factory=list)
    score_delta: float = 0.0
    prev_grade: str | None = None
    curr_grade: str | None = None
    feed_bytes_changed: bool = False
    size_delta: int | None = None
    expiry_delta: int | None = None

    @property
    def grade_moved(self) -> bool:
        return (
            self.prev_grade is not None
            and self.curr_grade is not None
            and self.prev_grade != self.curr_grade
        )

    @property
    def grade_dropped(self) -> bool:
        if not self.grade_moved:
            return False
        try:
            return _GRADE_ORDER.index(str(self.curr_grade)) < _GRADE_ORDER.index(
                str(self.prev_grade)
            )
        except ValueError:
            return False

    @property
    def has_findings_change(self) -> bool:
        return bool(self.new or self.resolved or self.changed)

    @property
    def has_changes(self) -> bool:
        """Whether anything worth showing moved between the two snapshots."""
        return (
            self.has_findings_change
            or self.grade_moved
            or round(self.score_delta, 1) != 0.0
            or self.feed_bytes_changed
            or bool(self.expiry_delta)
        )


def _findings(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map each finding code in an artifact to its display fields, across the
    measured categories. The first occurrence of a code wins (a code is not
    expected to repeat across categories)."""
    out: dict[str, dict[str, Any]] = {}
    for key in _MEASURED_CATEGORIES:
        cat = artifact.get("categories", {}).get(key, {})
        if cat.get("status") != "measured":
            continue
        for f in cat.get("findings", []):
            code = f.get("code")
            if code and str(code) not in out:
                out[str(code)] = f
    return out


def _count(finding: dict[str, Any]) -> int:
    raw = finding.get("count", 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def _expiry_days(artifact: dict[str, Any]) -> int | None:
    days = (
        artifact.get("categories", {})
        .get("freshness", {})
        .get("details", {})
        .get("days_until_expiry")
    )
    if isinstance(days, bool) or not isinstance(days, (int, float)):
        return None
    return int(days)


def diff_artifacts(prev: dict[str, Any], curr: dict[str, Any]) -> FeedDiff:
    """Compute the structured diff from the previous snapshot to the current one.

    Findings are matched by validator code: a code present now but not before is
    *new*, present before but not now is *resolved*, and present in both with a
    different instance count is *changed*. Severity and the plain-language "what"
    come from the current snapshot for new/changed findings and from the previous
    snapshot for resolved ones (its description is the last thing the reader saw).
    """
    prev_f = _findings(prev)
    curr_f = _findings(curr)

    new = [
        FindingChange(
            code=code,
            what=str(f.get("what", "")),
            severity=str(f.get("severity", "INFO")),
            prev_count=None,
            curr_count=_count(f),
        )
        for code, f in curr_f.items()
        if code not in prev_f
    ]
    resolved = [
        FindingChange(
            code=code,
            what=str(f.get("what", "")),
            severity=str(f.get("severity", "INFO")),
            prev_count=_count(f),
            curr_count=None,
        )
        for code, f in prev_f.items()
        if code not in curr_f
    ]
    changed = []
    for code, f in curr_f.items():
        if code not in prev_f:
            continue
        before, after = _count(prev_f[code]), _count(f)
        if before != after:
            changed.append(
                FindingChange(
                    code=code,
                    what=str(f.get("what", "")),
                    severity=str(f.get("severity", "INFO")),
                    prev_count=before,
                    curr_count=after,
                )
            )

    # Worst severity first, then the biggest movers, within each bucket.
    rank = {"ERROR": 0, "WARNING": 1, "INFO": 2}
    new.sort(key=lambda c: (rank.get(c.severity, 9), -(c.curr_count or 0)))
    resolved.sort(key=lambda c: (rank.get(c.severity, 9), -(c.prev_count or 0)))
    changed.sort(
        key=lambda c: (rank.get(c.severity, 9), -abs((c.curr_count or 0) - (c.prev_count or 0)))
    )

    prev_score = float(prev.get("overall", {}).get("score", 0.0))
    curr_score = float(curr.get("overall", {}).get("score", 0.0))

    prev_sha = prev.get("feed", {}).get("sha256")
    curr_sha = curr.get("feed", {}).get("sha256")
    feed_bytes_changed = bool(prev_sha and curr_sha and prev_sha != curr_sha)
    prev_size = prev.get("feed", {}).get("size_bytes")
    curr_size = curr.get("feed", {}).get("size_bytes")
    size_delta = (
        int(curr_size) - int(prev_size)
        if isinstance(prev_size, (int, float)) and isinstance(curr_size, (int, float))
        else None
    )

    prev_days, curr_days = _expiry_days(prev), _expiry_days(curr)
    expiry_delta = (
        curr_days - prev_days if prev_days is not None and curr_days is not None else None
    )

    return FeedDiff(
        prev_date=str(prev.get("snapshot_date", "")),
        curr_date=str(curr.get("snapshot_date", "")),
        new=new,
        resolved=resolved,
        changed=changed,
        score_delta=round(curr_score - prev_score, 1),
        prev_grade=prev.get("overall", {}).get("grade"),
        curr_grade=curr.get("overall", {}).get("grade"),
        feed_bytes_changed=feed_bytes_changed,
        size_delta=size_delta,
        expiry_delta=expiry_delta,
    )
