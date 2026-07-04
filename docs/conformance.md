# Conformance mark

The grade is a gradient from A to F. The conformance mark is a bright line: a
feed either earns it or it does not. An agency can put the mark on its developer
page as a credential, and a state program can point to it as a clear bar.

The mark does not change any category score. It reads the scores the pipeline
already computes and applies three pass/fail checks.

## What a feed must clear

All three must hold at once:

1. **Valid** — the GTFS validator finds no errors. Warnings and info notices do
   not block the mark; errors are the ones that break a rider's trip.
2. **Current** — the service calendar has not lapsed and is not inside the
   expiry window. A feed about to run out does not qualify until it is renewed.
3. **Accessible** — the feed states wheelchair access on at least 90% of stops
   and 90% of trips. This measures what the feed publishes, not whether a stop
   is physically usable.

A feed that misses is shown as "not yet", with the specific gap named, never as
a failure.

## What gets published

When a feed earns the mark, the pipeline writes two files next to its artifacts:

- `mark.svg` — an embeddable seal, written only when the mark is earned, so the
  file's presence is the credential. A feed that later loses the mark has the
  seal removed.
- `conformance.json` — the machine-readable result (`awarded`, `status`, the
  three criteria with `met` and a plain-language detail). Always written.

The agency page shows the mark, the three checks, and a copy-paste embed when
the mark is earned.

## Embedding

When earned, copy the snippet from the agency page, or build it directly:

```markdown
[![GTFS conformance mark](https://<site>/data/artifacts/<agency-id>/mark.svg)](https://<site>/agency/<agency-id>/)
```

## Why these three

The mark extends the NTD readiness pillars (published, valid, current) with the
accessibility floor that the rubric already treats as a values statement. It is
the same shape a small agency is asked to meet for federal certification, plus
the accessibility data riders depend on. The official check for certification is
still the agency's own D-10.
