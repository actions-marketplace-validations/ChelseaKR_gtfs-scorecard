# 0011: Reuse MobilityData validation from the Mobility Feed API

Status: accepted (2026-06)

## Context

The MobilityData Java validator is the most expensive step in a score. The
sha-keyed validator cache (vcache.py) already skips a re-run when a feed is
byte-identical to the last run we did. But the first time we see a feed, and
after a validator upgrade, we still run Java.

The Mobility Feed API (api.mobilitydatabase.org) publishes, for each feed it
tracks, the latest dataset it fetched: a content hash, a hosted copy of the zip,
and a validation report run with a named gtfs-validator version, including a link
to the full report.json. When MobilityData has already validated the exact bytes
we hold, with the validator version we use, their report is our report.

## Decision

Add an optional ingest path (feedapi.py) that, on a cache miss, asks the Feed API
for the feed's latest dataset and reuses its validation report instead of running
Java, but only when every guard passes:

1. The agency pins an `mdb_id` and a Feed API token is set
   (`MOBILITY_FEED_API_TOKEN`).
2. The dataset's content hash equals the sha256 of the bytes we fetched.
3. The dataset's `validator_version` equals ours.
4. The full report.json is fetchable from the dataset's `url_json`.

On any miss, or any network or parsing error, the path returns None and the
pipeline runs the validator exactly as before. The reused report is parsed by the
same `parse_report_data` the local run uses and stored in the same vcache, so
downstream code cannot tell the source apart.

## Why the hash guard is non-negotiable

A feed scored against a report for different bytes would be wrong in a way no
test downstream would catch. The hash match is what makes reuse safe: if the
agency's origin feed differs from MobilityData's hosted dataset by even one byte,
we re-validate. This trades some cache hits (the two copies often differ) for
never publishing a mismatched score.

## Consequences

- A cost lever, not a correctness change: the grade is identical whether the
  report came from us or from MobilityData, because it is the same validator
  output for the same bytes.
- The token is optional. Without it, nothing changes. This keeps the default
  path dependency-free and the feature opt-in for a deployment that has Feed API
  credentials.
- `scorecard feedapi <feed-id>` exposes the same lookup for inspection, so an
  operator can see a feed's dataset, hash, and validation summary without
  scoring it.
- We do not auto-discover or ingest the full feed list yet; that is a larger
  follow-on. This decision covers the validation-reuse lever only.
