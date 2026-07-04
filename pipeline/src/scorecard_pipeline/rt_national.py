"""A national view of GTFS-Realtime reliability.

The realtime monitor records, per agency, a longitudinal series of uptime and
header-lag observations in ``data/rt-health`` (ADR 0012), and each agency page
already shows that agency's reliability (``render_site._rt_health_section``). What
the per-agency view cannot answer is the national one a data team or a state
program asks: of the agencies that publish a realtime feed, how many are actually
reliable, and how fresh is the data when it arrives?

This rolls the per-agency ``RtHealth`` summaries up into one national picture: a
reliability-band distribution, the national median uptime and freshness, a
per-state breakdown, and the most reliable feeds. It is pure over the summaries
the monitor already produces, so the artifact is reproducible and adds no polling.
It stays inside the serverless model: it reads the samples the Actions cron
already records and does not stand up a continuous worker fleet. Absence of a
realtime feed is shown as "not monitored", never as a zero, the same way a missing
realtime feed is neutral on a scorecard.

Reliability is the share of monitor runs where the feed responded (uptime); it is
not a grade input and changes no score.
"""

from __future__ import annotations

from typing import Any

from ._stats import _median

# Reliability bands by uptime (share of monitor runs the feed responded to). The
# breakpoints separate feeds a rider can count on from ones that flap, without
# pretending a single dropped sample is an outage. "Reliable" sits at 99% because
# realtime is meant to be always-on; "spotty" below 90% is where a rider would
# notice the gaps.
RELIABLE_THRESHOLD = 99.0
MOSTLY_THRESHOLD = 90.0

# An agency needs at least this many observations before it is ranked, so a feed
# monitored once does not top the "most reliable" list on a single lucky sample.
MIN_OBSERVATIONS = 3


def reliability_band(uptime_pct: float) -> str:
    """The reliability band for an uptime share.

    ``reliable`` at or above 99%, ``spotty`` below 90%, ``mostly`` in between.
    Three plain buckets so the national picture reads without a chart.
    """
    if uptime_pct >= RELIABLE_THRESHOLD:
        return "reliable"
    if uptime_pct >= MOSTLY_THRESHOLD:
        return "mostly"
    return "spotty"


def national_rt(summaries: list[dict[str, Any]], *, top: int = 10) -> dict[str, Any]:
    """Roll per-agency realtime-health summaries up into the national picture.

    Each summary carries at least id, name, state, observations, uptime_pct, and
    median_lag_seconds (the ``RtHealth`` fields plus identity). Agencies with no
    observations are dropped (they are not monitored, shown neutrally elsewhere).
    Reports how many agencies are monitored, the reliability-band distribution, the
    national median uptime and median header lag, a per-state breakdown, and the
    most reliable feeds (ranked by uptime then freshness, requiring a minimum
    number of observations). Pure and deterministic, safe to re-run. ``top`` caps
    the highlight list so the artifact stays light.
    """
    monitored = [s for s in summaries if int(s.get("observations", 0)) > 0]
    bands = {"reliable": 0, "mostly": 0, "spotty": 0}
    uptimes: list[float] = []
    lags: list[float] = []
    by_state: dict[str, dict[str, Any]] = {}
    for s in monitored:
        uptime = float(s["uptime_pct"])
        bands[reliability_band(uptime)] += 1
        uptimes.append(uptime)
        if s.get("median_lag_seconds") is not None:
            lags.append(float(s["median_lag_seconds"]))
        state = s.get("state") or "Unlocated"
        bucket = by_state.setdefault(
            state, {"state": state, "agencies": 0, "_uptime": [], "reliable": 0}
        )
        bucket["agencies"] += 1
        bucket["_uptime"].append(uptime)
        if reliability_band(uptime) == "reliable":
            bucket["reliable"] += 1

    states = []
    for state in sorted(by_state, key=lambda s: (-by_state[s]["agencies"], s)):
        b = by_state[state]
        med = _median(b["_uptime"])
        states.append(
            {
                "state": state,
                "agencies": b["agencies"],
                "median_uptime_pct": round(med, 1) if med is not None else None,
                "reliable": b["reliable"],
            }
        )

    rankable = [s for s in monitored if int(s.get("observations", 0)) >= MIN_OBSERVATIONS]
    most_reliable = sorted(
        rankable,
        key=lambda s: (
            -float(s["uptime_pct"]),
            float(s["median_lag_seconds"]) if s.get("median_lag_seconds") is not None else 1e9,
            s.get("name", s.get("id", "")),
        ),
    )[:top]

    median_uptime = _median(uptimes)
    median_lag = _median(lags)
    return {
        "monitored_count": len(monitored),
        "bands": bands,
        "median_uptime_pct": round(median_uptime, 1) if median_uptime is not None else None,
        "median_lag_seconds": int(median_lag) if median_lag is not None else None,
        "states": states,
        "most_reliable": [
            {
                "id": s["id"],
                "name": s.get("name", s["id"]),
                "state": s.get("state") or "Unlocated",
                "uptime_pct": round(float(s["uptime_pct"]), 1),
                "median_lag_seconds": s.get("median_lag_seconds"),
            }
            for s in most_reliable
        ],
    }
