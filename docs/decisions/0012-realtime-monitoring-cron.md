# 0012: Realtime monitoring on an Actions cron, not a worker fleet

Status: accepted (2026-06)

## Context

No canonical tool tracks GTFS-Realtime quality over time. The realtime validator
is point-in-time, and our own realtime category scores one sampling window per
daily run. That answers "how is the feed now", not "how reliable has it been".

The expansion plan (docs/expansion.md, Phase B) names continuous national
realtime as the feature that forces a worker fleet: the Cal-ITP archiver polls
every feed every 20 seconds into object storage. That is the right architecture
at national scale and on the spec's 30-60s cadence. It is also the one Phase B
piece that breaks the project's serverless, single-digit-dollar constraint, so
standing it up is a deliberate, funded step, not a default.

## Decision

Build the serverless tier first: a GitHub Actions cron (`rt-monitor.yml`) that,
every few hours, takes a short sampling burst of each agency's realtime feeds and
appends one small observation per agency to `data/rt-health/<id>.json`. The
record is summarized into uptime and median header lag and shown on each agency
page.

The pure pieces (`rt_health.py`: derive an observation from a window, summarize a
record) carry the logic and are unit-tested. Sampling reuses the existing
`capture_window`, and the monitor stays a pure realtime poll: it does not
download the static feed, so it is cheap and fast. Trip coverage, which needs the
schedule, stays with the daily score.

## Why a cron is enough for now

At the pilot and early-national scale, with a handful of agencies publishing
realtime, the questions a small agency and a state liaison actually ask are "is
my realtime feed up" and "how fresh is it". A cron answers both: uptime as the
share of checks where the feed responded, freshness as the median header lag.
What a cron cannot do is observe at 30-60s resolution, so it undercounts brief
outages between runs. That is an accepted limitation of this tier, stated on the
page ("sampled on a schedule").

## Escalation trigger

Move to the worker-fleet pattern (a queue, pollers on the spec cadence, object
storage, the Cal-ITP `gtfs-rt-archiver` design) when either holds:

- the realtime cohort grows past what a single cron run can sample politely, or
- a user needs sub-minute outage detection or per-trip realtime history.

Until then the cron tier ships the capability at no new cost, and the record
format (a list of observations) is forward-compatible with a higher-cadence
producer writing the same shape.

## Consequences

- Realtime reliability is visible now, serverless, and within budget.
- The data is coarser than a true archiver and can miss short outages; the page
  says so.
- `data/rt-health` is committed like the other artifacts, so history survives the
  ephemeral runner and rides the same Pages deploy.

## Update (high-cadence session built)

The middle tier between the cron and a worker fleet is built (`rt_archiver.py`
plus the manual `rt-archive.yml`). A bounded archiving *session* polls one
agency's realtime feeds on the spec's 20-second cadence for a fixed window in a
single job, recording a high-resolution observation per round (a ten-minute
session is thirty observations). `scorecard rt-archive --agency <id> --duration
600 --interval 20` runs it; the session schedule is pure and unit-tested, and each
round is summarized with the same rt_health code, so the always-on worker fleet
(the final escalation, which needs the user's cloud) would write the identical
record shape. This closes most of the resolution gap without operating a fleet.
