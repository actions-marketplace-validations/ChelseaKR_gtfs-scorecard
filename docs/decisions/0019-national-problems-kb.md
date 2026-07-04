# 0019: National "most common problems" knowledge base

Status: accepted (2026-06)

## Context

The corpus holds every agency's findings (canonical validator notices and the
scorecard's own plain-language checks), each already rewritten as a fix. No one
has aggregated that across feeds to answer the practitioner's and the journalist's
question: what are the most widespread GTFS problems in the country, and what is
the one fix for each? The expansion-research ideation flagged this as the
highest-value, lowest-risk next build because it reuses data already on disk.

## Decision

Add a national problem-prevalence rollup and a `/problems/` page.

- `findings_national.agency_findings` extracts one agency's distinct findings
  (deduplicated by code across categories).
- `findings_national.national_problems` rolls those up into per-code prevalence:
  how many feeds carry each problem, the share that is, total instances, the
  severity, the source (validator vs scorecard), and a representative what/why/fix.
- `render_site` aggregates the findings it already reads in pass 1 (no second
  read), writes `api/v1/problems.json`, and renders `/problems/`.

## Why prevalence is a share of all feeds, not only affected feeds

`total_agencies` is the scored count, so a problem on 574 of 1,113 feeds reads as
51.6%, not 100% of the feeds that happen to have it. The honest denominator keeps
the headline numbers defensible for the press and for policy.

## Framing

Consistent with the standing principles: prevalence is presented as a common,
shared, fixable problem ("most feeds trip on the same handful of things"), never
as a ranking of who is worst, and it changes no grade. The page leads a manager
toward a fix that probably applies to them, and points at the existing
`/fix/<code>/` guides where one exists.

## Consequences

- The rollup is pure and unit tested; it adds no per-agency work because it reuses
  the pass-1 read.
- `prevalence_by_code` is published for every code (not just the top 25), so a
  later change can add a "this affects N% of US feeds" line to each `/fix/<code>/`
  guide. That augmentation is deferred to avoid reordering the fix-page render
  (the guides render before the artifact pass today).
- The page is wired into the nav, footer, sitemap, the API index, and the pa11y
  accessibility gate, like the other national views (ADRs 0017, 0018).
