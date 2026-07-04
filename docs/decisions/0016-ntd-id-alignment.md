# 0016: NTD ID alignment as a forward-looking flag, not a grade input

Status: accepted (2026-06)

## Context

Aligning the GTFS `agency_id` field with the agency's five-digit NTD ID lets a
published feed join cleanly to its NTD record. The October 2024 proposed rule
would have *required* that alignment in the feed; the
[July 2025 final rule](https://www.federalregister.gov/documents/2025/07/10/2025-12813/national-transit-database-reporting-changes-and-clarifications-for-report-years-2025-and-2026)
did **not** adopt it, after 15 of 18 commenters opposed a mandated feed-side
change, and instead collects the `agency_id`-to-NTD-ID link on the agency's P-50
form. So this is a useful, optional convention, not a federal requirement the
agency must satisfy in its GTFS.

Surfacing the alignment still helps the small and rural agencies this tool serves
join their feed to their NTD record, and the service plan (Stage 5) calls for
flagging it. We show it as an optional improvement, framed as a fix and never as
a penalty.

> **Update (2026-06-30, RESEARCH-ROADMAP R7):** the original draft of this ADR and
> the copy it drove said FTA "requires" `agency_id` to equal the NTD ID. That was
> the October 2024 *proposed* rule, which the July 2025 final rule softened to the
> P-50 crosswalk. The readiness copy in `ntd.py`, `render_site.py`, `config.py`,
> and `docs/crosswalk.md` was corrected to the final-rule framing (optional
> alignment, not a mandated feed change). The decision below is unchanged.

Two facts shape how we can check it:

- We can only *verify* alignment when we know the agency's NTD ID. For the curated
  pilots we do; for the national Mobility Database cohort we usually do not.
- The `agency_id` field is optional in GTFS when a feed has a single agency, so a
  blank `agency_id` is valid GTFS even though it is not NTD-aligned.

## Decision

Add the NTD ID to the registry as an optional `ntd_id` and check `agency_id`
against it as a standalone, zero-deduction flag in the NTD readiness section.

- `gtfs.read_agency_ids` reads the distinct `agency_id` values from agency.txt.
- `ntd.assess_id_alignment(feed_agency_ids, ntd_id)` returns one of `aligned`,
  `mismatch`, `missing`, or `unknown`, each with plain-language detail and, when
  there is an action, a concrete fix.
- The result rides on the artifact as `ntd_id_alignment` and renders below the
  published/valid/current pillars on the static scorecard page.

It is **not** a fourth readiness pillar and does not affect the readiness status
or any category grade.

## Why a separate flag, not a pillar

The three readiness pillars (published, valid, current) each apply to every feed
and combine into a single certify-readiness status. Alignment is different on both
counts: it is only checkable when we have the NTD ID, and it is a distinct
requirement from "is this feed certifiable today." Folding it into the readiness
status would, for the many feeds where we have no NTD ID, either invent an
"unknown" pillar that drags the status down or silently pass it. Keeping it
adjacent lets the status stay honest while the flag still surfaces the
requirement.

## Why neutral when the NTD ID is unknown

The product principles say findings are framed as fixes and absence is shown
neutrally, the way a missing realtime feed is never a zero. When we have no NTD ID
on file we cannot tell whether a feed is aligned, so the status is `unknown` with
a short note about the requirement and no fix or penalty. This mirrors the
state-level equity overlay degrading to "unknown" rather than failing
([ADR 0015](0015-equity-overlay-state-level.md)).

## Consequences

- The two pilots (Unitrans `90142`, Yolobus `90090`) get a real aligned or
  mismatch read; everyone else sees a neutral, educational note until their NTD ID
  is curated in.
- Adding an NTD ID is a one-line registry edit (`ntd_id: "NNNNN"`), so a curator
  or a supporter can turn the check on per agency without code.
- Zero grade impact, consistent with the other attached blocks (recommendations,
  conformance, routability).
- Older artifacts without the block render exactly as before; the renderer omits
  the line when `ntd_id_alignment` is absent.
