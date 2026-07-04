# 0017: Persona-facing surfaces over data we already publish

Status: accepted (2026-06)

## Context

An expansion research pass ([docs/expansion-research.md](../expansion-research.md))
asked how the scorecard could widen its service: more for the three personas it
serves, new personas, public features, and research/policy uses. The honest
finding was that most of the underlying data already exists. The pipeline already
computes NTD readiness per feed and rolls it up nationally (ADR 0016, `ntd.json`),
records accessibility-field coverage per feed (ADR 0006), and publishes a static
cross-agency API (ADR 0013). What was missing was not data; it was the surfaces
that turn that data toward specific people the research named:

- FTA and state-DOT program staff, who have a federal reason to care about NTD
  readiness but had no page that reads the national `ntd.json`.
- Disability and accessibility advocates, who care whether feeds carry
  wheelchair data at all. The site had an accessibility *statement* page but no
  view of accessibility-data *coverage* across feeds.
- The agency manager facing a vendor, who can require quality in a contract but
  had nowhere to copy the language from.

## Decision

Add three pages, each built at render time from artifacts already on disk, each
zero grade impact:

- `/ntd/` renders the national and per-state certification-readiness numbers from
  the same `ntd.json` the pipeline already writes.
- `/access/` renders a national accessibility-data coverage view (the share of a
  feed's stops carrying `wheelchair_boarding`, nationally and per state, with the
  most complete feeds highlighted). It is backed by a new pure module
  `access.py` (`coverage_record`, `national_coverage`) and a new API endpoint
  `api/v1/accessibility.json`.
- `/procurement/` is a static copy-paste contract/RFP clause that asks a vendor to
  deliver a feed passing the canonical validator and staying current.

`/ntd/` joins the primary nav; the other two sit in the footer and on the data
page. All three go in the sitemap and the pa11y accessibility gate.

## Why these, and why not more

The research surfaced many ideas, but most were already shipped (machine-readable
JSON/CSV/Parquet, a national map GeoJSON, the liaison/board one-page brief, the
equity overlay, vendor accountability). Building those again would have added
surface without value. These three are the gaps that were real: each serves a
named persona, and each reads data the pipeline already produces, so the cost is a
render function and a small pure module rather than new ingestion.

## Why no grade impact

Consistent with the standing principles and ADR 0016: accessibility coverage and
NTD readiness are lenses, framed as coverage to build on and a heads-up to act on,
never a penalty. The accessibility page is careful to say it measures whether the
*data* exists, not whether a stop is physically accessible.

## Consequences

- `access.py` is pure over the per-agency artifacts the renderer already reads, so
  the new artifact is reproducible and adds no per-agency work.
- Older artifacts without the accessibility fields are skipped by
  `coverage_record` rather than counted as zero coverage, so the national average
  never understates coverage because of a stale artifact.
- The deferred bigger bets (national realtime-quality monitoring beyond the
  current point samples, and bulk NTD-ID population from the Transitland Atlas
  crosswalk to turn ID-alignment on past the two pilots) are recorded in
  [docs/expansion-research.md](../expansion-research.md) for a later session.
