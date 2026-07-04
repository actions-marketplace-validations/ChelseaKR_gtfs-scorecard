# 0009 — Pathways and levels awareness (first slice)

Status: accepted
Date: 2026-06-20

## Context

GTFS `pathways.txt` and `levels.txt` describe how a rider moves through a
station: the walkways, stairs, escalators, elevators, and fare gates connecting
entrances, platforms, and levels. For a multi-level station or a shared hub, this
is the layer that tells a trip planner how to route someone inside the station,
and it is the layer that tells a wheelchair user whether a step-free (elevator)
route exists. The accessibility sub-score (ADR 0006) measures whether stops state
wheelchair boarding; pathways are the next layer of accessible navigation.

Most small and rural agencies, the project's core audience, publish flat feeds:
stops with no stations, entrances, or pathways. That is complete and correct for
them, and the scorecard must not flag it. Pathways only become relevant once a
feed models stations or entrances.

As with the flex and fares slices, this environment cannot fetch a real
station feed, so the slice is built and tested on fixtures, and the
gtfs-validator covers the structural validity of the pathways graph.

## Decision

Add pathways and levels awareness as a first slice that is relevant only to feeds
that model stations, and that never penalizes a flat stop-only feed.

1. **Detect station modeling and pathways.** From `stops.txt` location types,
   whether the feed has stations (location_type 1) or entrances (location_type
   2); and whether it carries `pathways.txt` and `levels.txt`. Also whether any
   pathway is an elevator (pathway_mode 5), a step-free signal.

2. **Flag only the real gap.** When a feed models stations or entrances but has no
   pathways, a trip planner cannot route riders through the station and there is
   no step-free route information. That gets a finding framed as a fix. A flat
   feed with no stations gets nothing, no finding and no noise.

3. **Acknowledge what is there.** When a feed has pathways, surface it neutrally,
   noting step-free (elevator) routes when present. A "Station pathways" chip
   appears, the same neutral treatment flex and seasonal service get.

4. **No grade change in this slice.** The findings carry a zero deduction, so they
   inform and guide without moving the completeness score or the overall grade.
   Pathways live inside Rider experience as detail and findings, not a new
   category. We do not flag the absence of elevators: a single-level station
   legitimately has none, and that is a physical fact, not a data gap.

## Consequences

- A hub or station agency gets a concrete, accessibility-relevant nudge when it
  models stations but omits the pathways that let riders navigate them.
- A flat small-agency feed is untouched, in keeping with the project's rule that
  a simple feed is not an incomplete one.
- No existing agency's grade moves: findings are zero-deduction and detection
  only fires on feeds that model stations.
- The slice confirms pathways are present and whether a step-free route is
  described, not that the station graph is correct or complete (the validator
  covers structure). Grading pathway completeness is a later decision that needs
  real station feeds to calibrate.
