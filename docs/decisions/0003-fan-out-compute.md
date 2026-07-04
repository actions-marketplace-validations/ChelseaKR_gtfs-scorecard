# ADR 0003: Fan-out compute for the daily run at country scale

Status: proposed · Date: 2026-06-12

## Context

The validator runs in a few seconds per feed (ADR 0001), so the daily run is
embarrassingly parallel and cheap per unit. Year 1 of the roadmap handles
growth by sharding the GitHub Actions cron into a parallel matrix (the
`scorecard shards` command and `scorecard.yml`). That carries a region's worth
of feeds inside the free Actions minutes.

Two things eventually outgrow the matrix. First, a daily run over a couple
thousand feeds wants a queue with elastic concurrency rather than a fixed
matrix sized in YAML. Second, realtime quality needs sustained polling across
service windows, which a cron job is poorly suited to.

## Decision

Keep the Actions matrix as the default through Year 1. For Year 2, add a
serverless fan-out in `infra/compute/`, not as a rewrite but as a second runner
for the same CLI:

- EventBridge schedule invokes a producer Lambda (`enqueue.py`) that reads the
  registry and drops one SQS message per agency.
- A pool of worker Lambdas (`worker.py`, a JVM container image so the validator
  runs in-process) drains the queue, each scoring one agency with the existing
  `scorecard run` and uploading that agency's artifacts to the bucket from
  ADR 0002. Concurrency is a single setting; raising it scales the run.
- A collect step rebuilds `index.json` and rollups after the queue drains, the
  same race-free split the sharded CI workflow uses (`scorecard reindex`).
- Realtime sampling runs as a scheduled Fargate task over defined windows
  (a morning peak, a midday, an evening peak), writing raw protobuf snapshots
  the daily scoring job consumes. Scheduling it to windows, not always-on,
  keeps it the largest but still small line item.

## Consequences

- The pipeline code does not change. The worker is a thin wrapper, because the
  pipeline is a filesystem CLI; moving runners is a packaging change. This is
  ADR 0001's bet paying off a second time.
- Cost tracks usage: validation bills per millisecond of worker time, and the
  sampler bills per window. The single-digit-dollars budget holds into Year 2.
- This stays "proposed" until an agency count actually strains the matrix.
  Standing it up early would add operational surface with nothing to show for
  it. The Terraform and handlers are written so the switch is an apply, not a
  project.
