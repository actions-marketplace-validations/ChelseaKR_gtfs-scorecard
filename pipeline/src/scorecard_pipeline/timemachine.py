"""Feed time-machine: a plain-language timeline of what changed across an agency's
score history.

The trend chart shows the shape; this narrates it. From the dated history the
pipeline already keeps, it derives a text event for each snapshot where something
changed: a grade move, the feed crossing into or out of the expiry window, or a
notable score swing, naming the category that drove it. A reader, including one
using a screen reader, gets the story without reading a chart.

True GTFS-file diffing (which routes or stops changed) needs the raw feed, which
is not archived; this works from the artifacts on hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .metrics import expiry_status

# Friendly category names; "completeness" shows as "rider experience" in the UI.
_CAT_LABELS = {
    "correctness": "correctness",
    "freshness": "freshness",
    "completeness": "rider experience",
    "realtime": "realtime",
}

MIN_SCORE_MOVE = 3.0


@dataclass(frozen=True)
class Event:
    date: str
    kind: str  # grade_change | expiry | score_move
    detail: str


def _driver(prev_cats: dict[str, Any], curr_cats: dict[str, Any]) -> str | None:
    """The category that moved most between two snapshots, as a phrase, or None
    when nothing moved meaningfully."""
    best_label: str | None = None
    best_delta = 0.0
    for key, label in _CAT_LABELS.items():
        if key in prev_cats and key in curr_cats:
            delta = float(curr_cats[key]) - float(prev_cats[key])
            if abs(delta) > abs(best_delta):
                best_delta = delta
                best_label = label
    if best_label is None or abs(best_delta) < MIN_SCORE_MOVE:
        return None
    verb = "rose" if best_delta > 0 else "fell"
    return f"{best_label} {verb} {abs(round(best_delta))} points"


def _expiry_phrase(prev_status: str, curr_status: str, days: Any) -> str:
    if curr_status in ("lapsed", "stale"):
        return "Feed expired."
    if curr_status == "expiring_soon":
        tail = f" ({int(days)} days of service left)" if isinstance(days, (int, float)) else ""
        return f"Feed entered the expiry window{tail}."
    if curr_status == "current" and prev_status in ("expiring_soon", "lapsed", "stale"):
        return "Feed renewed to a current calendar."
    return f"Feed status changed to {curr_status}."


def history_events(
    history: list[dict[str, Any]], *, min_score_move: float = MIN_SCORE_MOVE
) -> list[Event]:
    """A plain-language event per snapshot where something changed, newest first.

    One event per transition, choosing the most salient change: a grade move wins,
    then an expiry-window crossing, then a notable score swing. A steady feed
    produces nothing."""
    events: list[Event] = []
    for prev, curr in zip(history, history[1:], strict=False):
        date = str(curr.get("date", ""))
        prev_grade, curr_grade = prev.get("grade"), curr.get("grade")
        prev_score, curr_score = prev.get("score"), curr.get("score")
        prev_exp = expiry_status(prev.get("days_until_expiry"))
        curr_exp = expiry_status(curr.get("days_until_expiry"))
        driver = _driver(prev.get("categories", {}), curr.get("categories", {}))

        if curr_grade != prev_grade and curr_grade is not None and prev_grade is not None:
            detail = f"Grade went {prev_grade} to {curr_grade}"
            events.append(Event(date, "grade_change", detail + (f", {driver}." if driver else ".")))
        elif curr_exp != prev_exp:
            phrase = _expiry_phrase(prev_exp, curr_exp, curr.get("days_until_expiry"))
            events.append(Event(date, "expiry", phrase))
        elif (
            isinstance(prev_score, (int, float))
            and isinstance(curr_score, (int, float))
            and abs(curr_score - prev_score) >= min_score_move
        ):
            verb = "rose" if curr_score > prev_score else "fell"
            detail = f"Score {verb} {abs(round(curr_score - prev_score))} points"
            events.append(Event(date, "score_move", detail + (f", {driver}." if driver else ".")))

    return list(reversed(events))
