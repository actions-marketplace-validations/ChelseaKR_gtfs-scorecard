# Listing policy

This is a short, plain statement of what the scorecard lists, why, and how an
agency can correct or remove its listing. It exists because the tool grades
public agencies by name, and the people it is built for deserve to know the
rules.

## What is listed, and why

The scorecard checks **public GTFS feeds** that an agency already publishes
openly, and grades the data quality. We list an agency to help it (and the
people who support it) see how the feed is doing and what to fix first. The
sources are public feed catalogs (the Mobility Database, transit.land) and
agency-submitted feeds.

## What the grade is, and is not

The grade is a **data-quality and completeness lens** meant to help an agency
improve its feed. It is **not** the official Caltrans or Cal-ITP compliance
determination, and it is not a verdict on the agency's service. A low grade
usually means the feed is expiring or missing optional fields, not that the
buses are bad. Findings are framed as fixes, never as failures, and an agency
that does not publish realtime is shown neutrally, never penalized for it.

## How to correct or remove a listing

We will act on these quickly and without argument:

- **Correct a name, URL, or detail** that is wrong: open an issue or a pull
  request against [`agencies.yaml`](../agencies.yaml), or email the address in
  the repository.
- **Request removal**: an agency that does not want to be listed can ask to be
  removed, by the same channels. We honor removal requests; the entry is deleted
  and the agency is excluded from future runs.
- **Report a feed that has moved or broken**: tell us and we will update or drop
  the URL.

## Long-expired feeds

A feed whose calendar ran out over a year ago is shown in its own group on the
directory, separate from the recently lapsed ones. Two cases hide in that group,
and we tell them apart by hand rather than by the grade:

- **The agency still runs and the export lapsed.** A curator can record this with
  an `operating_note` in [`agencies.yaml`](../agencies.yaml) after confirming the
  service still operates. The scorecard and directory then show the verified note,
  so the feed reads as recoverable rather than defunct.
- **The service genuinely ended.** When an agency has stopped operating, the entry
  is retired: it is removed from `agencies.yaml` and excluded from future runs, the
  same as any removal request. We do not leave a permanent failing grade on an
  agency that no longer exists.

The registry is curated, so every entry can be reviewed, corrected, or removed
by a person. If something here is wrong or unwelcome, that is a bug, and we want
to fix it.
