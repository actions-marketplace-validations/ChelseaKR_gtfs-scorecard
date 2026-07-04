# ADR 0001: Where the gtfs-validator runs

Status: accepted · Date: 2026-06-11

## Context

The MobilityData gtfs-validator is a Java CLI (v8.0.1, Java 17+). The
pipeline shells out to it rather than reimplementing validation rules. The
question from CLAUDE.md's open questions: Lambda, Fargate, or a GitHub
Actions cron?

Measured locally on the pilot feeds (both under 500 KB zipped): the
validator completes in a few seconds well within default JVM memory. These
are small feeds; this will hold for any agency this tool targets.

## Decision

Phase 1: the pipeline runs locally via `scorecard run --all`; the validator
jar is downloaded once into `data/cache/` and invoked as a subprocess.

Phase 2 (scheduled runs): GitHub Actions on a daily cron, committing or
uploading the JSON artifacts to the static host. Actions gives us Java 17,
cron, secrets, and logs with zero infrastructure to maintain, and the
artifacts-only contract means the web app never knows the difference.

A Lambda container image (JVM base) stays on the table for Phase 4 if run
frequency or agency count outgrows Actions. Fargate is overkill at these
feed sizes.

## Consequences

- No AWS footprint is required to reach the demo; CloudFront + S3 (or even
  GitHub Pages) only needs to serve static files.
- Run cost stays at zero, under the single-digit dollars/month budget.
- Pipeline code stays runtime-agnostic: everything is a plain CLI working
  against the filesystem, so moving to Lambda later is a packaging change,
  not a refactor.
