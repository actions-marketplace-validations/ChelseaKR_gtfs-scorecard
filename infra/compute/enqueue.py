"""Producer: fan the daily run out onto the work queue.

Year 2 of docs/roadmap.md. When the agency count outgrows the GitHub Actions
matrix, an EventBridge schedule invokes this Lambda once a day. It reads the
registry and drops one message per agency onto SQS; a pool of worker Lambdas
(worker.py) drains the queue in parallel. The work is one independent unit per
agency, so this scales by raising worker concurrency, not by changing code.

Reuses the pipeline's own registry loader so "the list of agencies" has exactly
one definition across the batch and serverless paths.
"""

from __future__ import annotations

import json
import os
from typing import Any

import boto3

from scorecard_pipeline.agencies import load_agencies
from scorecard_pipeline.config import AGENCIES

QUEUE_URL = os.environ["WORK_QUEUE_URL"]


def handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    load_agencies()
    sqs = boto3.client("sqs")
    sent = 0
    for batch_start in range(0, len(AGENCIES), 10):
        chunk = sorted(AGENCIES)[batch_start : batch_start + 10]
        sqs.send_message_batch(
            QueueUrl=QUEUE_URL,
            Entries=[
                {"Id": str(i), "MessageBody": json.dumps({"agency_id": agency_id})}
                for i, agency_id in enumerate(chunk)
            ],
        )
        sent += len(chunk)
    return {"enqueued": sent}
