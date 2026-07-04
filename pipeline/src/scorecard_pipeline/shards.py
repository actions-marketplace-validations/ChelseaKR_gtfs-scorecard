"""Split the agency list into balanced shards for parallel CI runs.

The roadmap's Year 1 compute step (docs/roadmap.md): the validator is a few
seconds per feed, so a region's worth of feeds still fits the daily cron, but
only if the work fans out instead of running in one serial loop. The CI matrix
asks this command for a plan, then each matrix job runs its slice with
`scorecard run --agency ...`.

Round-robin assignment keeps shards close to equal in size without needing to
know per-feed timing. A single rebuild job stitches the per-shard artifacts
back into one index afterwards.
"""

from __future__ import annotations


def plan_shards(agency_ids: list[str], count: int) -> list[list[str]]:
    """Distribute agency ids across `count` shards, round-robin.

    Empty shards are dropped so the CI matrix never spawns a job with no work
    (which happens when there are fewer agencies than requested shards).
    """
    if count < 1:
        raise ValueError("shard count must be at least 1")
    buckets: list[list[str]] = [[] for _ in range(count)]
    for i, agency_id in enumerate(sorted(set(agency_ids))):
        buckets[i % count].append(agency_id)
    return [b for b in buckets if b]
