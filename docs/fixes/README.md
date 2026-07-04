# Notice-to-fix knowledge base

Every finding the scorecard surfaces carries a one-line fix. This is where
those fixes grow into short, practical how-tos, keyed by the validator notice
code (or the scorecard's own code for metrics the validator does not cover).

It is the most durable thing the project builds. A finding tells an agency what
is wrong; a fix page tells them which setting to change in the tool they
actually use. The roadmap (docs/roadmap.md) calls this out as a cross-cutting
piece worth starting early and never finishing, because it gets better with
every agency conversation.

## How it is organized

One file per code, named for the code: `docs/fixes/<code>.md`. Each page has the
same short structure so a CSM can read it aloud on a call:

- **What this means** in plain language.
- **Why it matters** to a rider or to the agency.
- **How to fix it**, with the common scheduling tools named where the setting
  differs between them.
- **How long it usually takes.**

The frontend can deep-link to these pages from a finding by its code, so the
"Fix" line on a scorecard becomes a link to the full walkthrough.

Each page also links to the finding's **canonical rule**: the matching
MobilityData gtfs-validator notice, a GTFS Best Practice, or the GTFS Schedule
reference. That mapping is data, not prose: it lives in
`pipeline/src/scorecard_pipeline/rule_links.py`, and `tests/test_rule_links.py`
asserts every page here has an entry and vice versa, so adding a page without a
rule mapping fails CI. See ADR 0024.

## Pages so far

These cover the codes seen across the tracked agencies, grouped by the scorecard
category that surfaces them.

Correctness (validator notices):

- [`expired_calendar`](expired_calendar.md)
- [`feed_expiration_date7_days`](feed_expiration_date7_days.md)
- [`feed_expiration_date30_days`](feed_expiration_date30_days.md)
- [`service_has_no_active_day_of_the_week`](service_has_no_active_day_of_the_week.md)
- [`trip_coverage_not_active_for_next7_days`](trip_coverage_not_active_for_next7_days.md)
- [`service_window_outside_feed_period`](service_window_outside_feed_period.md)
- [`missing_required_column`](missing_required_column.md)
- [`missing_recommended_file`](missing_recommended_file.md)
- [`missing_feed_contact_email_and_url`](missing_feed_contact_email_and_url.md)
- [`mixed_case_recommended_field`](mixed_case_recommended_field.md)
- [`route_color_contrast`](route_color_contrast.md)
- [`invalid_currency_amount`](invalid_currency_amount.md)
- [`fast_travel_between_consecutive_stops`](fast_travel_between_consecutive_stops.md)
- [`stop_too_far_from_shape_using_user_distance`](stop_too_far_from_shape_using_user_distance.md)
- [`unknown_column`](unknown_column.md)
- [`unknown_file`](unknown_file.md)
- [`unused_shape`](unused_shape.md)
- [`stop_without_stop_time`](stop_without_stop_time.md)

Rider experience completeness (scorecard codes):

- [`scorecard_missing_headsigns`](scorecard_missing_headsigns.md)
- [`scorecard_wheelchair_boarding_unknown`](scorecard_wheelchair_boarding_unknown.md)
- [`scorecard_wheelchair_accessible_unknown`](scorecard_wheelchair_accessible_unknown.md)
- [`scorecard_no_fare_data`](scorecard_no_fare_data.md)
- [`scorecard_no_feed_contact`](scorecard_no_feed_contact.md)

Freshness (scorecard codes):

- [`scorecard_missing_feed_info_dates`](scorecard_missing_feed_info_dates.md)

The backlog is the rest of the MobilityData notice taxonomy: a code gets a page
as soon as it shows up in a tracked agency's findings.
