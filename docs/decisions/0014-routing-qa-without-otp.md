# 0014: Router-free trip-plannability checks before OpenTripPlanner

Status: accepted (2026-06)

## Context

A feed can pass structural validation and still be unusable: a trip with one
stop, a stop no trip serves. The expansion plan (docs/expansion.md, Phase C)
proposes loading each feed into OpenTripPlanner and asserting that sample trips
return itineraries, which catches breakage the validator misses.

OTP is a full Java routing service. Standing one up per feed, building a graph,
and running sample queries is heavy: minutes of build time per feed, a JVM and
memory budget, and operational surface. That is the opposite of the project's
serverless, single-digit-dollar constraint, and most of what OTP would catch on a
small-agency feed is reachable with cheaper structural checks.

## Decision

Build the serverless tier first: `routability.py`, two pure checks over the
feed's tables that catch the most common "validates but unusable" gaps without a
router.

- Single-stop trips: a trip with fewer than two stop_times has no rideable leg.
- Orphan stops: a boardable stop (location_type 0 or blank) that no trip serves.

Both are zero-deduction findings, sharing the additive-finding pattern used for
flex and pathways, so they name the gap without moving the grade. They run in the
normal scoring pass and attach to the artifact for the page.

## Why this is enough for now

On a small-agency feed, the failures that make a trip unroutable are
overwhelmingly these two shapes, and both are exact, not heuristic. A full router
adds value on large multi-modal networks (transfers that don't connect, walk legs
that don't reach, timed connections that just miss), which is the right reason to
escalate, not the common small-agency case.

## Escalation trigger

Add an OpenTripPlanner job (its own optional CI workflow or a Fargate task,
gated like the other heavy infra) when either holds:

- the rubric wants to assert real itineraries between sample origin/destination
  pairs, not just structural rideability, or
- the cohort includes large multi-agency networks where transfer and timed-
  connection correctness matters.

The structural checks stay regardless, as the cheap first pass that runs on every
feed.

## Consequences

- A real "can a rider use this" signal ships now, serverless, on every feed.
- It is narrower than OTP: it does not verify that an actual A-to-B itinerary
  exists, only that trips have legs and stops have service.
- Zero-deduction, so the grade is unchanged; this is guidance, not a new penalty.

## Update (OTP glue built, run gated)

The OTP integration is built as the gated escalation (`otp.py` plus the manual
`otp-qa.yml` workflow). It samples origin/destination stop pairs that span the
service area, builds OTP plan requests, parses the responses, and decides whether
the sampled trips routed: `scorecard otp --base <otp-url> --feed <zip>` exits
non-zero when a sampled trip returns no itinerary, so a CI job can gate on it. The
selection, request building, parsing, and verdict are pure and unit-tested. What
stays gated is the OTP service itself: building a graph per feed is the heavy step
the user runs (or points the workflow at), not something the daily run does. The
router-free structural checks remain the always-on first pass.
