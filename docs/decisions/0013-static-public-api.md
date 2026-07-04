# 0013: A static public API before a warehouse

Status: accepted (2026-06)

## Context

The dashboard answers one agency at a time. The cross-agency questions (who ranks
where, which feeds moved, how a state compares) need a query surface. The
expansion plan (docs/expansion.md, "Cross-agency trends and a public API")
sketches a warehouse: DuckDB or Athena over partitioned object storage, with a
keyed read API via API Gateway, or transit.land's Go + Postgres + GraphQL model
if interactive queries appear.

The architecture decision tree in the same doc orders the build cheapest first:
client-side search, then a queryable artifact over object storage, then a managed
database only if interactive multi-tenant queries appear. The cross-agency views
people actually ask for are small and bounded: a list, a leaderboard, per-state
aggregates, national stats.

## Decision

Serve those views as a versioned set of flat JSON files under `api/v1/`,
precomputed at render time from the same index the site trends from, and served
from the same object storage as the pages. No query server, no key, no rate
limit. Per-agency detail is not duplicated: it stays each agency's published
artifact, which the API index points to.

`publicapi.py` holds pure builders over the index dict, so every endpoint is
reproducible and unit-tested. The endpoints are `index`, `agencies`,
`leaderboard`, `by-state`, and `stats`; a human `/leaderboard/` page renders the
same standings.

## Why not the warehouse now

A warehouse and a keyed API are real operational surface: a query engine to run,
usage plans to manage, a cost that scales with queries. The current need is
bounded, cacheable reads that a static file serves for free with better latency
and no failure mode. Building the warehouse now would add cost and operations
for a query flexibility no consumer has asked for.

## Escalation trigger

Move to a query layer (DuckDB or Athena over the partitioned artifacts) when a
consumer needs arbitrary filtering or joins, or full per-agency history at a
scale that makes precomputed files unwieldy. Add a managed database and a keyed
API only if interactive multi-tenant queries appear after that. The static
endpoints stay as the cache-friendly front for the common reads regardless.

## Update (query layer shipped)

The DuckDB query layer is built (`warehouse.py`), as the first half of that
escalation and still serverless: the national table is published as
`api/v1/agencies.parquet`, and `scorecard query` runs DuckDB over the dataset in
process (no server, the `query` extra). A DuckDB or Athena consumer queries the
Parquet directly. A managed database is still gated on interactive multi-tenant
queries actually appearing; the Parquet plus the static JSON cover the reads seen
so far.

## Consequences

- Cross-agency data ships now, versioned and documented, within budget.
- `v1` is a contract: additive changes only; breaking changes go to `v2`.
- The endpoints are recomputed every render, so they never drift from the pages.
- Bulk analysis is still better served by the single `dataset.json` / `.csv`
  table; the API is for targeted cross-agency reads.
