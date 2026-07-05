"""Shared statistical helpers."""

from __future__ import annotations

_GRADES = ("A", "B", "C", "D", "F")


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _percentile(score: float, peers: list[float]) -> int:
    """Percent of peers this score is at least as good as (0-100).

    Defined inclusively so the best score reads as 100 and ties don't punish an
    entity for sharing a common score. ``peers`` includes the entity itself.
    """
    if not peers:
        return 0
    at_or_below = sum(1 for p in peers if p <= score)
    return round(100 * at_or_below / len(peers))
