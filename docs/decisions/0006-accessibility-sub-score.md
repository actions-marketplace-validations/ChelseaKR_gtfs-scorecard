# 0006 — Break accessibility out as its own sub-score

Status: accepted
Date: 2026-06-20

## Context

Accessibility fields carry 40 of the 100 points in the Rider experience
completeness category: `wheelchair_boarding` on stops (25) and
`wheelchair_accessible` on trips (15). The rubric weights them this heavily on
purpose, as both a values statement and the most common real gap in
small-agency feeds.

The weight was there, but a reader could not see it. The agency page showed one
completeness score and a single "Accessibility gaps" chip that fired whenever the
whole completeness score fell below 70. That proxy was wrong in both directions:
a feed with excellent accessibility but no fare data tripped the chip, and a feed
with poor accessibility but everything else filled in could miss it. The audience
includes people who review accessibility for a living, so burying it inside a
blended score undersells the one thing the project most wants to foreground.

## Decision

Surface accessibility as its own 0-100 sub-score, derived from the two
accessibility components already computed (earned accessibility points over the
40 available). It is a lens on the existing completeness math, not a new category
and not a change to the overall grade or the weights.

- The pipeline publishes a structured `accessibility` block in the completeness
  category details: the sub-score, the share of stops and trips that state
  accessibility, the share marked accessible versus not accessible, and an
  explicit `measures: presence_not_usability` flag.
- The agency page shows the sub-score inside the Rider experience card, with the
  caveat that it measures what the feed states, not whether a stop is physically
  usable.
- The "Accessibility gaps" chip now keys off the accessibility sub-score, not the
  blended completeness score.

The web app reads already-published artifacts, which predate the structured
block, so the renderer derives the same sub-score from the `components` the
current artifacts already carry and prefers the structured block when present.
No re-score is required for the sub-score to appear.

## Consequences

- Accessibility gets the prominent, honest placement the rubric always intended,
  and the chip stops misfiring.
- The number is "states accessibility," not "is accessible." The
  presence-not-usability caveat travels with it everywhere it appears, so a high
  sub-score is never misread as verified physical access. A later expansion can
  add plausibility checks (a stop marked accessible with no path data is still
  only a claim).
- The overall grade and category weights are unchanged, so no agency's letter
  moves because of this.
