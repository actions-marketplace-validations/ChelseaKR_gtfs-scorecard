# 0008 — Fares v2 awareness (first slice)

Status: accepted
Date: 2026-06-20

## Context

The Rider experience completeness category scored fares as present or absent: 15
points if the feed carries any fare files, zero otherwise (plus the fare-free
opt-out from ADR earlier). That binary check misses the modern failure mode.

GTFS-Fares v2 splits a fare into pieces: `fare_products.txt` is the thing a rider
buys, and `fare_leg_rules.txt` says which trips a product applies to. A feed can
publish fare products and still show riders no fare, because nothing wires those
products to any leg. That is not a validator error: an orphan product is
structurally valid GTFS, so the gtfs-validator passes it. But to a trip planner
the fare is invisible, which is exactly the rider-facing gap this project exists
to translate.

As with flex (ADR 0007), this environment cannot fetch a real Fares v2 feed, so
the slice is built and tested on fixtures, and we lean on the validator for the
structural validity of the fare files rather than reimplementing it.

## Decision

Add fare-model awareness as a first slice that names what a feed publishes and
catches the published-but-not-applied gap, without changing anyone's grade.

1. **Classify the fare model.** `none`, `legacy` (Fares v1 `fare_attributes`), or
   `v2` (`fare_products`). A feed can carry both; v2 is reported when products
   are present.

2. **Check that fares are applied.** Fares are usable when a trip planner can show
   them: a v1 flat fare is usable on its own, and a v2 feed is usable when it has
   leg rules wiring products to trips. A v2 feed with products but no leg rules is
   "published, not applied," and gets a finding framed as a fix.

3. **Report it qualitatively, not as a contestable number.** This slice surfaces
   the model and the applied/not-applied status as plain text, not a 0-100
   sub-score. A numeric fares depth score would be a new scoring judgment that
   needs real feeds to calibrate, and a number that did not move the grade would
   sit oddly next to the accessibility sub-score, which does reflect graded
   points. Whether to grade fare depth is a separate, later decision.

4. **No grade change in this slice.** The fares findings carry a zero deduction,
   so they inform and guide under "everything we checked" without moving the
   completeness score or the overall grade. The existing binary 15-point fares
   component is unchanged, and the fare-free opt-out still suppresses all of this.

## Consequences

- A feed that publishes fare products but never applies them now gets a clear,
  rider-facing nudge, where before it looked complete to the binary check and
  clean to the validator.
- No existing agency's grade moves: the findings are zero-deduction and the
  graded fares component is untouched.
- The new `fares` detail block (model, product count, whether leg and transfer
  rules exist, applied flag) is available to consumers and to a later slice that
  may grade fare depth once there are real Fares v2 feeds to tune against.
- It surfaces only after a re-score, since already-published artifacts predate the
  `fares` block; the daily run carries it in.
