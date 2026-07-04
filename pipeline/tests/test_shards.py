"""Tests for the CI fan-out shard planner."""

from __future__ import annotations

import pytest

from scorecard_pipeline.shards import plan_shards


def test_round_robin_balances_shards() -> None:
    shards = plan_shards(["a", "b", "c", "d", "e"], 2)
    assert shards == [["a", "c", "e"], ["b", "d"]]


def test_every_agency_appears_exactly_once() -> None:
    ids = [f"a{i}" for i in range(23)]
    shards = plan_shards(ids, 4)
    flat = [x for shard in shards for x in shard]
    assert sorted(flat) == sorted(ids)


def test_empty_shards_are_dropped() -> None:
    shards = plan_shards(["a", "b"], 5)
    assert shards == [["a"], ["b"]]


def test_zero_shards_rejected() -> None:
    with pytest.raises(ValueError):
        plan_shards(["a"], 0)
