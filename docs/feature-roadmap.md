# Feature roadmap

A near-term, feature-level plan: the concrete things to build next and the order
to build them in. This sits between the two longer-horizon documents and should
be read with them:

- [`product-roadmap.md`](product-roadmap.md) is the multiyear view of user value.
- [`roadmap.md`](roadmap.md) is the multiyear infrastructure and scaling plan.
- This file is what to ship over the next few iterations, with a first step and a
  definition of done for each item, so the next session can pick one up cold.

It is a planning document, not a commitment. Revise it as the pilot teaches us
what agencies and their liaisons actually use. Every item is checked against the
principles in `product-roadmap.md`: findings framed as fixes, no leaderboard, we
score on top of the canonical validator, accessibility gets prominent placement.

## Where this picks up

The directory now separates expired feeds from the rest and splits them into
recently lapsed (likely still running, a re-export fixes it) and long expired
(the source stopped refreshing). A `scorecard discover` command checks every
tracked feed URL against the Mobility Database and reports whether a newer
canonical feed exists. Run against the 63 expired feeds, it found that none have
moved: every dead URL is still the one the agency or its vendor lists, so the
staleness is at the source. See [`feed-discovery.md`](feed-discovery.md).

That result sets the agenda. The biggest quality gap in the corpus is not wrong
URLs on our side; it is feeds that quietly stopped updating. The first theme below
turns the scorecard from something that observes that problem into something that
helps a liaison act on it.

## Competitive sequence

[ADR 0005](decisions/0005-competitive-positioning.md) sets the posture:
independent, national, agency-first. No existing tool combines daily monitoring,
a plain-language grade, prioritized fixes, trends and alerts, and national
coverage. Cal-ITP's reports are monthly PDFs and California-only; MobilityData's
validator is on-demand HTML. The wedges below ride on that gap, in order, each
earning the next:

1. **Robust fetching, then national coverage.** Breadth is the moat a state
   program cannot match, and it depends on a fetcher that survives the WAF and
   User-Agent blocks that currently fail government-hosted feeds (capitol-corridor,
   yolobus, ridgecrest). Fix the fetch, then drain the Mobility Database.
2. **Cross-standard view.** Promote the crosswalk from a credibility footnote to a
   per-agency feature mapping one grade to every program at once.
3. **Vendor accountability.** Build out the operator vendor view into the public,
   attention-getting angle no government program will take.

These reorder the themes below: the "Later" coverage and registry items move up,
and a new robust-fetch item leads. The expired-feed loop still ships first because
it is nearly done and proves the agency-first thesis.

## Now: close the expired-feed loop

The data says 63 of 134 measured feeds are expired and 43 of those have been dead
over a year. The tool already names the problem. These features help someone fix
it.

### Resilient feed fetching (coverage prerequisite)

- **Why.** National coverage is the competitive foundation (ADR 0005), and it is
  blocked today by feeds that return 403 to an automated fetch: capitol-corridor,
  yolobus, and ridgecrest fail every run while the agencies still operate. A
  scorecard that cannot fetch a third of real feeds cannot go national.
- **First step.** Send a browser-realistic User-Agent and `Accept` headers from
  `net.py`, retry with backoff on 403/429, and fall back to the agency's
  Mobility Database `direct_download` when the registry URL is blocked. Record
  the fetch failure as a neutral "feed unreachable" state, distinct from a low
  grade, so a blocked feed never reads as the agency's fault.
- **Done when.** The three known-blocked pilot-region feeds score again, and a
  fetch failure is visible as its own state rather than a stale snapshot.

### Recurring stale-feed report, per program

- **Why.** A Caltrans-district or Cal-ITP-style liaison wants a worklist: which of
  my agencies have a lapsed feed, how long ago, and is it the recoverable kind.
- **First step.** Add an `expired` section to each program rollup artifact
  (`rollups.py`), counting lapsed vs stale members and listing them worst-first,
  the same split the directory uses.
- **Done when.** Every program page (`/program/<id>/`) shows its expired feeds in
  the two buckets, and the cohort view in the app can filter a saved cohort down
  to its lapsed feeds.

### `discover` on a schedule, replacements as pull requests

- **Why.** A canonical URL will eventually move for some agency. We should catch
  it automatically rather than scoring a dead link for months.
- **First step.** Add a weekly CI job that runs `scorecard discover --expired` and
  uploads the report as an artifact; when it finds a `replaced` agency, open a pull
  request that updates that `static_gtfs_url` in `agencies.yaml` for human review.
- **Done when.** A moved feed surfaces as a reviewable pull request within a week,
  and `docs/feed-discovery.md` is regenerated by the job rather than by hand.

### "Still operating?" signal for the long-expired bucket

- **Why.** A feed dead over a year splits into two very different cases: the agency
  still runs and the export lapsed, or the service itself ended. The grade should
  not read the same for both, and a liaison needs to know which call to make.
- **First step.** Add an optional `operating_note` field to `agencies.yaml` a
  curator can set after a manual check, rendered on the scorecard and the directory
  so a confirmed-still-running feed reads as recoverable.
- **Done when.** The long-expired group can carry a human-verified status, and the
  listing-and-removal policy covers retiring a feed whose agency has genuinely
  stopped.

### Liaison-ready outreach copy

- **Why.** The fastest path to a fixed feed is a liaison forwarding the agency one
  clear paragraph. We already write the fix; we can write the message.
- **First step.** For an expired feed, generate a short, copy-pasteable note that
  names the agency, what lapsed, the rider impact, and the one export setting to
  change, reusing the freshness finding text.
- **Done when.** Each expired scorecard has a "copy a note to the agency" block,
  and the email digest links to it.

## Next: make freshness predictive, not just observed

Today freshness is measured the day a feed expires or after. These features warn
earlier and carry the signal into the places people already look.

### Expiry forecasting and lead-time alerts

- **Why.** The valuable alert arrives weeks before expiry, while there is calm time
  to re-export, not after riders lose trip planning.
- **First step.** In the alert digest (`alerts.py`), tier upcoming expirations by
  lead time (60, 30, 14, 7 days) using `days_until_expiry`, so a subscriber sees a
  ramp rather than a single cliff-edge warning.
- **Done when.** A subscriber gets a first heads-up at the 60-day mark and the
  digest groups feeds by how soon they expire.

### Expiry status in the public API and badges

- **Why.** Consumers of the public artifacts should be able to act on freshness
  without recomputing it, and a badge that flips to "feed expired" is a strong,
  passive nudge on an agency's own site.
- **First step.** Document `expiry_status` and `days_until_expiry` in
  [`api.md`](api.md), bump the catalog and index `schema_version` for the additive
  fields, and add an expiry state to the badge (`badge.py`).
- **Done when.** `api.md` describes the freshness fields with stable values, and a
  badge shows feed status, not only the letter grade.

### Show which findings cleared between runs

- **Why.** A manager who changed one export setting wants to see that specific fix
  land, not just a category score tick up. This is the strongest retention signal.
- **First step.** Diff the findings codes between an agency's two most recent
  artifacts and render a "fixed since last check" list on the scorecard.
- **Done when.** Clearing a finding shows up by name on the next day's scorecard
  and in the "what changed" summary.

## Later: registry quality and reach

Groundwork that pays off as coverage grows past one region. These build on the
discovery work but are not blocking the loop above.

### Pin Mobility Database ids in the registry

- **Why.** Name-token matching in `discover` is a heuristic. Storing each feed's
  `mdb_id` makes re-discovery exact and lets us follow the catalog's own record of
  a feed when its URL changes.
- **First step.** Add an optional `mdb_id` to `agencies.yaml` and have the sync and
  discover commands prefer an exact id match over name matching when it is present.
- **Done when.** Tracked feeds carry their catalog id and `discover` reports by id,
  not by fuzzy name.

### Realtime freshness alongside schedule freshness

- **Why.** The freshness category is schedule-only today. An RT feed can go stale
  the same silent way, and the rubric already reserves realtime as a category.
- **First step.** Extend the realtime metric to flag a header timestamp that lags
  well past the sampling interval, and surface it with the same lapsed framing.
- **Done when.** A stale RT feed reads as a freshness problem, not a missing-feed
  zero.

### Vendor view of stale feeds

- **Why.** 53 of the 63 expired feeds share one hosting vendor. A pattern that
  large is a finding a statewide program can act on once, upstream, instead of
  agency by agency.
- **First step.** Aggregate expiry status by feed host or detected export tool and
  show the counts on an internal program view, kept private and framed as where to
  spend support time, never as a public ranking.
- **Done when.** A program staffer can see that one vendor accounts for most stale
  feeds in their cohort.

## How to use this list

Pick the top unstarted item under "Now" unless a pilot agency or liaison asks for
something specific. Keep each feature shippable on its own: a finished pull request
that renders, passes ruff, mypy, and pytest, and updates the relevant doc. When an
item ships, move it out of this file and into the "where the product is today"
paragraph in `product-roadmap.md`.
