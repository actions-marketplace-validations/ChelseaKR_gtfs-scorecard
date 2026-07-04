# ADR 0002: Publish artifacts to S3 behind CloudFront as the registry grows

Status: accepted · Date: 2026-06-12

## Context

Phase 1 through Phase 3 commit one JSON artifact per agency per day to git and
serve them from GitHub Pages (ADR 0001). This is free and boring and right for
two pilot agencies. The rollout roadmap (docs/roadmap.md) takes the registry to
a region (50 to 200 agencies) and then a country (thousands). Committing a file
per agency per day makes the git history noisy at fifty and untenable at a few
hundred, and Pages serves from the repository, so the two problems are linked.

The web app reads pre-computed JSON and nothing else. That contract is the
asset here: the frontend never knew whether a URL was Pages or a CDN.

## Decision

Move published artifacts to an S3 bucket fronted by CloudFront, keeping the
exact `<agency>/<date>.json`, `latest.json`, `index.json`, and `rollups/` paths
the web app already reads. The bucket is private; CloudFront reaches it through
Origin Access Control. The Terraform is in `infra/artifacts/`.

The pipeline does not learn about S3. It stays a filesystem CLI (the principle
from ADR 0001). The daily workflow's collect job runs `aws s3 sync` after it
rebuilds the index, gated on an `ARTIFACTS_BUCKET` repository variable, so the
pilot and forks that set no variable keep serving from Pages with no change.

The frontend points at the CDN through one optional setting in
`web/src/config.js` (`SCORECARD_DATA_BASE`), left null until the bucket exists.

## Consequences

- Git history stops carrying daily artifact churn once the sync is enabled; the
  artifacts in the repo become a convenience copy, not the system of record.
- Cost stays within budget: at thousands of small JSON files refreshed daily,
  S3 and CloudFront are cents to low single-digit dollars a month.
- The move is reversible and incremental. Turning the variable off falls back
  to Pages. Nothing in the data contract changes, so no artifact needs
  reformatting.
- A short CloudFront TTL (default 300s) keeps the site current without a
  per-deploy invalidation.
