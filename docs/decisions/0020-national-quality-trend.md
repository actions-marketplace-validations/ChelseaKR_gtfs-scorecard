# 0020: National quality trend, with a stable-cohort guard

Status: accepted (2026-06)

## Context

Each agency page trends its own score. The question one level up, "is transit
data quality improving nationally?", is one a journalist or a program would ask,
and the published index already holds every agency's dated history, so the series
can be derived without new stored state.

## Decision

Add `national_trend.as_of_points`, which carries each agency's most recent score
forward to each date in the corpus and averages, producing a national daily
series (average score, grade mix, expired share). `render_site` writes
`api/v1/trend.json` and a `/trends/` page with an autoscaled line chart.

## The composition trap, and the guard

The naive series is actively misleading. The corpus was assembled over the window:
two pilot feeds on the first days (averaging in the high seventies), then a
hundred, then eleven hundred (averaging in the low sixties). Charting that as the
national average would show a 17-point "decline" that is entirely a change in
*which* feeds are counted, not in their quality. Publishing "transit data is
getting worse" off a composition artifact would be wrong and damaging.

So `as_of_points` drops any date whose agency count is below `min_coverage` (0.8)
of the series' peak, leaving the window where the cohort is stable enough to
compare. On today's data that yields the nine days from the corpus reaching full
size, over which the average has held steady. The page accrues value as more days
land, and the headline only ever compares like with like.

## The chart autoscales

National averages move in a narrow band, so the line chart scales its y-axis to
the data range (not a fixed 0 to 100) and names that range in the SVG text
alternative, so a small real move is visible without overstating it.

## Consequences

- Pure and reproducible from the index; no new persisted state, no per-agency
  work. Unit tested, including the coverage guard.
- The series is honest by construction: it never compares a tiny early cohort to
  the full corpus.
- Wired into the footer, sitemap, the API index, and the pa11y gate, like the
  other national views (ADRs 0017–0019). It changes no grade.
