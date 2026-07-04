# Expansion research, round two: features, data, audiences, integrations

A deep-research pass (2026-07-01) across four axes of continued expansion,
building on [`expansion-research.md`](expansion-research.md) (the verified
competitive research), [`expansion-ideation-2026-07.md`](expansion-ideation-2026-07.md)
(the horizon scan, now mostly implemented), and the shipped surface as of
today: the six-hub IA, /pulse/, /focus/, /check/, /query/, /compare/, the MCP
server, monthly dataset releases, and the Canada pilot. Everything below is
new relative to those documents, with sources cited inline. Items are tagged
**buildable now**, **partnership-gated**, or **bet**.

## 1. Features

### Detect cEMV support (buildable now)

The GTFS community adopted the `cemv_support` field on 2025-09-29 (4 in
favor, none against): agencies and routes can now declare that riders can pay
with contactless bank cards
([PR #545](https://github.com/google/transit/pull/545)). This is exactly the
shape of signal the What-feeds-publish page tracks. Detection is a column
read in agency.txt/routes.txt, the same pattern as `flex.py`; adoption today
is near zero, which is the point: the page can watch a brand-new field spread
from day one. Frame as adoption, never quality, as with the rest.

### Realtime prediction accuracy has a ready-made methodology (bet, de-risked)

The ideation doc called RT prediction accuracy "the next honest frontier"
gated on the always-on archive. The methodology risk is now retired: the
community maintains a
[GTFS-Realtime prediction accuracy metrics](https://docs.google.com/document/d/1-AOtPaEViMcY6B5uTAYj7oVkwry3LfAQJg3ihSRTVoU/edit)
definition, MBTA published an open-source
[transit-performance](https://github.com/mbta/transit-performance) system
measuring prediction accuracy in production, and Mineta published an
[assessment methodology](https://transweb.sjsu.edu/mctm/research/utc/Assessing-GTFS-Accuracy)
for temporal accuracy of TripUpdates. When the archive bet is funded, the
metric definitions should be adopted from these rather than invented.

### The independent-referee position sharpened (strategy, not a build)

The vendor market consolidated around exactly this problem:
[Optibus acquired Trillium](https://blog.optibus.com/announcements/optibus-expands-in-north-america-with-acquisition-of-trillium)
and now markets GTFS services on the claim that "more than 90% of feeds
receive first-pass approval from Google"
([Optibus](https://blog.optibus.com/optibus-launches-gtfs-services-and-in-platform-gtfs-enhancements-to-improve-passenger-trust-and-meet-compliance));
[Swiftly acquired Hopthru](https://www.goswift.ly/blog/swiftly-hopthru-acquisition-announcement)
to sell ridership cleaning and NTD reporting. Vendors now market quality
claims a buyer cannot verify. The scorecard is the only national,
independent, daily check of those claims, and the procurement page should
say so explicitly: the acceptance test works precisely because the referee
is not selling the feed.

## 2. Data

### NTD ridership via API, unblocking ADR 0021 (buildable now)

FTA's 2024 annual data products are out, and monthly ridership now lives on
data.transportation.gov with a Socrata API
([Complete Monthly Ridership, dataset 8bui-9xvu](https://data.transportation.gov/Public-Transit/Complete-Monthly-Ridership-with-Adjustments-and-Es/8bui-9xvu);
[NTD annual metrics by agency](https://data.transportation.gov/Public-Transit/NTD-Annual-Data-View-Metrics-by-Agency-/g27i-aq2u)).
Ridership weighting (ADR 0021) has been gated on a hand-committed CSV; a
weekly fetch keyed on `ntd_id` removes that gate and keeps the numbers
current. Ridership context also improves the compare page and the brief
("a 2M-trips-a-year agency" reads differently than "an agency").

### Canada at registry scale (buildable now)

Statistics Canada consolidates GTFS from about 150 Canadian agencies in the
[Canadian Public Transit Network Database](https://www150.statcan.gc.ca/n1/en/catalogue/23260003),
and the federal geospatial platform maintains
[canada-gtfs](https://github.com/federal-geospatial-platform/canada-gtfs)
tooling. The Canada pilot runs three agencies; the discovery pathway for
fifty-plus more exists, with provincial licenses already documented by
[Metrolinx](https://www.metrolinx.com/en/about-us/open-data),
[BC Transit](https://www.bctransit.com/open-data/), and
[TransLink](https://www.translink.ca/about-us/doing-business-with-translink/app-developer-resources/gtfs/gtfs-data).
Growing Canada is now a registry-curation task, not an engineering one.

### Pathways beyond the feed (bet, watch)

The [OpenSidewalks](https://tcat.cs.washington.edu/opensidewalks/) schema and
the [OpenThePaths 2026](https://tcat.cs.washington.edu/otp2026/) program are
building statewide pedestrian-path data with transit providers, with an
interoperability plan for trip planners. The scorecard measures whether a
feed publishes accessibility data; OpenSidewalks measures whether the
sidewalk to the stop exists. A future stop-area walkability lens would join
the two. Not buildable yet; worth citing in the access methodology and
watching the interoperability plan.

### GBFS is the adjacent corpus (buildable later)

The pipeline already carries a `gbfs.py` module, MobilityData ships a
[canonical GBFS validator](https://gbfs.org/tools/) with data-quality
reports, and GBFS is the de facto standard for shared micromobility in North
America. A "shared mobility" lens (does the city's bikeshare publish valid,
fresh GBFS?) reuses the whole scorecard pattern on a new corpus. Scope it
only after Canada scales; it is a second product surface, not a feature.

## 3. Audiences

### National RTAP and the tribal centers (partnership-gated, highest fit)

[National RTAP](https://www.nationalrtap.org/Technology-Tools/GTFS-Builder)
runs the free GTFS Builder used by rural and tribal agencies, holds weekly
GTFS office hours explicitly in support of the NTD requirement, and runs a
[tribal transit program](https://www.nationalrtap.org/Tribal-Transit/Tribal-Transit-Program);
DOT is standing up seven new
[TTAP centers](https://www.transportation.gov/grants/dot-navigator/tribal-technical-assistance-program-ttap).
These are the support desks for exactly the agencies the scorecard serves.
The concrete asks are small: /check/ and /try.html as office-hours tools, the
scorecard as the after-you-publish step in their GTFS Builder guide, and the
`ntd_note` field for waivered or shared-feed reporters they support. One
introduction email each; the product is already shaped for them.

### State DOT data programs as portfolio users (partnership-gated)

[WSDOT builds GTFS for any Washington agency that lacks it](https://learn.sharedusemobilitycenter.org/casestudy/transit-innovation-workshop-series-workshop-1-state-dot-support-for-the-general-transit-feed-specification-gtfs/)
and is launching a shared data archive with ODOT; ODOT maintains statewide
feeds through a single vendor and the GTFS-ride archive. These programs are
the liaison persona at state scale, and the per-state rollup pages are
already their portfolio view. The ask: show two state programs their own
/program/ page and the one-fix-from-ready NTD table, and learn what a state
data manager needs that a Cal-ITP-style CSM does not. Their archives are
also candidate partners for the RT-history bet, hosting the storage the
cost guardrail will not.

### Journalists via templated local stories (buildable now, validate first)

Local data journalism increasingly runs on shared national datasets:
[Big Local News](https://datajournalism.com/read/handbook/one/introduction/why-is-data-journalism-important)
partners national data with local newsrooms, and the UK's RADAR model
generates thousands of localized stories from one dataset. The monthly
dataset releases plus the by-state rollups are that shape already. A
"story-ready" cut per state (plain-language summary, the covered-set caveat
baked in, a reporter-facing methodology note) is one render away, and the
press-explainer item (E3 in the research roadmap) becomes its cover page.
The no-shaming framing must ride along or this audience is a net risk.

### Vendors, now with proof of demand (interview-gated, unchanged)

The Optibus/Trillium and Swiftly/Hopthru consolidations confirm vendors buy
and sell on data quality and NTD reporting. The vendor worklist stays gated
on one vendor interview per the research roadmap, but the interview target
list is now obvious: the post-acquisition data teams whose marketing depends
on quality claims an independent scorecard can confirm.

## 4. Integrations

### List the MCP server where agents look it up (buildable now)

The [official MCP Registry](https://registry.modelcontextprotocol.io/) is
the canonical, open feed of MCP servers and accepts listings without an
enterprise account. The
[Claude Connectors Directory](https://claude.com/docs/connectors/building/submission)
(511 connectors as of June 2026) requires a remote server, a privacy policy,
read-only tool annotations, and a Team/Enterprise submission, so it is a
later step that would require hosting the server remotely. Sequence:
registry listing now; connectors directory only if remote hosting ever
earns its keep against the cost guardrail.

### Contribute the crosswalk upstream (buildable now)

The [Transitland Atlas](https://github.com/transitland/transitland-atlas) is
explicitly "open to use as a crosswalk within other transportation data
systems," and MobilityData's
[awesome-transit](https://github.com/MobilityData/awesome-transit) list is
the discovery page the ecosystem actually reads. Two small acts of
ecosystem citizenship with distribution upside: a PR adding the scorecard to
awesome-transit, and publishing the scorecard's own id-to-mdb-to-onestop
crosswalk (the catalog already carries `mdb_id`) so consumers can join the
grades to either registry. The
[Transitland v2 REST API](https://www.transit.land/documentation/rest-api/)
is also a second discovery source for feed moves, complementing the
Mobility Database in `discover`.

### NTD Socrata API as a standing join (buildable now)

Same integration as the ridership item above, named here because it is an
integration pattern, not just a dataset: data.transportation.gov exposes the
NTD tables the crosswalk and ridership features need, keyed by the `ntd_id`
the registry already carries. One fetcher, several features fed.

## Sequencing recommendation

1. **Now, small:** cEMV detection on What-feeds-publish; MCP Registry
   listing; awesome-transit PR; publish the id crosswalk; NTD ridership
   fetcher unblocking ADR 0021.
2. **Next:** Canada registry growth from the StatCan corpus; the
   story-ready state cut with the press explainer.
3. **Outreach (human):** one email each to National RTAP and a state DOT
   data program; the vendor interview.
4. **Bets, unchanged but de-risked:** RT prediction accuracy (adopt the
   published metrics; court a state archive as host); stop-area walkability
   (watch OpenThePaths); GBFS lens (after Canada scales).

## Deliberate no's, restated

The cost guardrail and the no-shaming principle still bind every item. The
GBFS lens and remote MCP hosting are the two temptations most likely to
breach the single-digit-dollars budget; neither proceeds without a named
user. Nothing here makes the scorecard a feed editor or a vendor ranking.
