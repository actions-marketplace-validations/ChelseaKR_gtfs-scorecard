# 0005 — Competitive positioning: independent, national, agency-first

Status: proposed

## Context

The brief is to compete more directly with existing GTFS-quality tools,
including Cal-ITP. The landscape, verified June 2026:

- **Cal-ITP reports** ([reports.calitp.org](https://reports.calitp.org/)) run the
  canonical validator on every California provider **monthly**, compile a
  **per-agency PDF**, and are **California-only**, run by Caltrans with a helpdesk
  for technical assistance. Authoritative and established (reports since 2022),
  but slow-cadence, static, and framed around compliance, not the individual
  manager's "what do I fix today."
- **MobilityData's canonical validator**
  ([gtfs-validator.mobilitydata.org](https://gtfs-validator.mobilitydata.org/))
  is **on-demand**: upload a feed, get an HTML notice report. Its grading scheme
  is a **manual** qualitative rubric. It is the rule engine we build on, not a
  monitored scorecard with a grade, trend, or alerts.
- **transit.land / the Mobility Database** are catalogs and registries, not
  quality scorecards.
- **Google's Transit partner dashboard** is the real de-facto gate (a rejected
  feed falls off Maps), but it is private to the agency, not a public benchmark.

No tool combines daily monitoring, a plain-language letter grade, prioritized
top-three fixes, trend and alerts and badges, national coverage, and a mapping
across standards. That gap is the opening.

Competing with Cal-ITP carries a trap worth naming: it is a state program we
(a) cite for authority, (b) could white-label to, and (c) cannot out-fund or
out-mandate, and which can adopt anything we open-source. A head-on "replace
their dashboard" posture is the highest-conflict, lowest-probability path and
forecloses the partnership outcome.

## Decision

Position as **independent, national, vendor-neutral, agency-first**: implement
every standard, but serve the agency manager and the field liaison, not the
compliance mandate. Pursue the four postures as one nested sequence, not as
parallel bets. Each earns the next.

1. **National coverage, the foundation.** Score the ~2,500 US feeds in the
   Mobility Database, not two pilots. This is the one thing a California-only
   program structurally cannot match, and everything else compounds on breadth.
   It depends on a **robust fetcher**: the persistent 403s on government-hosted
   feeds (capitol-corridor, yolobus, ridgecrest) are WAF/User-Agent blocks, and
   they are a coverage blocker, not an edge case.
2. **Synthesis as the product, our existing core widened.** Grade plus three
   plain-language fixes against Cal-ITP's PDF and MobilityData's raw HTML;
   daily against monthly; trend, cleared-findings, and lead-time alerts (all
   shipped). Keep extending this lead; it is the felt difference.
3. **Cross-standard Rosetta, the differentiator.** Turn the crosswalk doc into a
   per-agency live view that maps one grade to every program at once: the
   California guidelines, the MobilityData grading scheme, Google Transit, and
   NTD/FTA. No single program will map to its peers' standards; a neutral tool
   can, and it answers the agency's real question ("am I OK for all of them?").
4. **Vendor accountability, the attention wedge.** Aggregate quality by the
   export tool or host that produced the feed (the operator vendor view, already
   built). A government program will not publicly name vendors that ship stale or
   broken exports; an independent project can, which is both leverage on upstream
   quality and a press story.
5. **Replace or white-label, the earned end-state.** The first four earn the
   coverage and credibility to either be adopted by programs (white-label, the
   larger business) or to compete for a dashboard contract. Treat "replace
   Cal-ITP" as an outcome of winning on experience and breadth, not a starting
   posture.

Public framing stays cooperative: independent, national, agency-first, never
"beat Cal-ITP." We implement the standards; we are the tool, not the enforcer.

## Consequences

- Defensibility is coverage, brand with agencies, the longitudinal national
  dataset, and badge-link-back network effects, not the scoring, which is open
  and copyable.
- The standards crosswalk stops being "shown for credibility" and becomes a
  first-class feature. That also resolves the contradiction of citing Cal-ITP for
  legitimacy while competing with it: the relationship is interoperability.
- Robust fetching is promoted to a Now priority, because national coverage
  depends on it. The government-feed 403s are the first concrete task.
- Risk: a competing posture could sour a Cal-ITP partnership that is plausibly
  the bigger outcome. Mitigated by the cooperative public framing and by keeping
  white-label an explicit goal (see `product-roadmap.md`, Year 3).
- This is a planning decision, not a build commitment. Revisit as the landscape
  and any conversation with Cal-ITP or MobilityData evolves.
