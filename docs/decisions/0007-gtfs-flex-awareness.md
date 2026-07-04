# 0007 — GTFS-Flex awareness (first slice)

Status: accepted
Date: 2026-06-20

## Context

GTFS-Flex describes demand-responsive service: dial-a-ride, zone, and on-request
trips that classic GTFS cannot express. It is exactly the service many small and
rural agencies actually run, and the project's open question #2 and its rural
mandate both point at it. Until now the scorecard saw flex feeds through a
fixed-route lens: `service_type: demand_response` softened Freshness, but the
rider-experience side was silent on flex, so a dial-a-ride agency's real
operation was invisible and the page implicitly judged it as an incomplete
fixed-route feed.

Two constraints shape how far this first slice goes. The MobilityData
gtfs-validator already validates the flex files, so Correctness covers their
structural validity and we should not reimplement that. And this environment
cannot fetch a real flex feed to validate scoring against, so the slice is built
and tested entirely on fixture feeds.

## Decision

Add flex awareness as a first slice that represents flex service and checks the
one thing that matters most to a rider, without changing anyone's grade.

1. **Detect flex by its files.** A feed is treated as flexible when it carries
   `locations.geojson`, `location_groups.txt`, or `booking_rules.txt`. This is
   the standard, reliable signal. We deliberately do not read `stop_times.txt`
   to sniff flex columns: that file is often very large and sits behind the
   reader's safety cap, and a real flex feed ships the flex files anyway.

2. **Check that a rider can book.** The rider-experience analog of a headsign for
   flex is "how do I reserve a trip." When a feed has flex service, we check that
   booking is reachable: at least one booking rule is real-time bookable, or
   carries a phone number, link, or message. A flex feed with no booking rules,
   or rules that never say how to book, gets a finding framed as a fix.

3. **No grade change in this slice.** The flex findings carry a zero deduction,
   so they appear under "everything we checked" and acknowledge or guide, but do
   not move the completeness score or the overall grade. Flex lives inside the
   existing Rider experience category as detail and findings; we do not add a
   fifth category or reweight the rubric. Whether booking completeness should
   become a graded component is a separate, later decision that needs real flex
   feeds to calibrate against.

4. **Surface it neutrally.** The agency page shows a "Flexible service" chip when
   flex is present, the same neutral treatment realtime and seasonal service get.

## Consequences

- A dial-a-ride or zone-service agency now sees its real operation represented,
  and gets one concrete, rider-protective check (can a rider book) framed as a
  fix, never a failure.
- No existing agency's grade moves, because the findings are zero-deduction and
  detection only fires on feeds that actually carry flex files.
- The slice is honest about its limits: it confirms flex is present and bookable,
  not that the zones or windows are correct (the validator covers structure). A
  later slice can add graded booking completeness and zone plausibility once
  there are real feeds to tune it on.
