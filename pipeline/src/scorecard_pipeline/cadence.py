"""Per-feed cadence tiers for the intraday refresh.

The intraday refresh (ADR 0010) checks feeds for change far more cheaply than a
full score, but checking all ~1,100 feeds on the tightest cadence is neither
polite to every host nor useful: most feeds are stable and change at most a few
times a year. This splits feeds into tiers so the ones where a change matters
soonest are checked every cycle, while the stable long tail is spread out.

Priority feeds (checked every cycle):
- realtime publishers, whose feeds change constantly and whose health is the
  point of the realtime category;
- feeds in the expiry danger or recovery window (expiring soon, or recently
  lapsed and likely to be re-exported), where catching the change early is the
  whole value.

Everything else is standard: checked once per period, with each feed assigned a
stable bucket from its id so the load spreads evenly across cycles instead of
hammering every host at once.

Pure and testable: the live check still happens in liveness.py.
"""

from __future__ import annotations

import hashlib
from typing import Any

from .metrics import expiry_status

PRIORITY = "priority"
STANDARD = "standard"

# How many cycles a standard feed waits between checks. With an hourly refresh
# this is once every six hours, spread across six buckets.
STANDARD_PERIOD = 6


def cadence_tier(artifact: dict[str, Any]) -> str:
    """Classify a feed from its latest artifact into a check cadence tier."""
    categories = artifact.get("categories", {})
    if categories.get("realtime", {}).get("status") == "measured":
        return PRIORITY
    days = categories.get("freshness", {}).get("details", {}).get("days_until_expiry")
    if expiry_status(days) in ("expiring_soon", "lapsed"):
        return PRIORITY
    return STANDARD


def _bucket(agency_id: str, period: int) -> int:
    """A stable 0..period-1 bucket for a feed, so standard checks spread evenly."""
    digest = hashlib.sha256(agency_id.encode()).hexdigest()
    return int(digest, 16) % period


def is_due(agency_id: str, tier: str, hour: int, *, period: int = STANDARD_PERIOD) -> bool:
    """Whether a feed should be checked on the cycle at `hour` (0-23)."""
    if tier == PRIORITY:
        return True
    return hour % period == _bucket(agency_id, period)


def due_now(tiers_by_id: dict[str, str], hour: int, *, period: int = STANDARD_PERIOD) -> list[str]:
    """The feed ids due to be checked on the cycle at `hour`, sorted."""
    return sorted(
        aid for aid, tier in tiers_by_id.items() if is_due(aid, tier, hour, period=period)
    )
