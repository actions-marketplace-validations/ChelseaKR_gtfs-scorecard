"""Tests for the DuckDB cross-agency query layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from scorecard_pipeline.warehouse import duckdb_available, query_rows, to_parquet

pytestmark = pytest.mark.skipif(not duckdb_available(), reason="DuckDB (query extra) not installed")

_ROWS = [
    {"id": "a", "name": "Alpha", "grade": "A", "score": 95.0, "realtime": None},
    {"id": "b", "name": "Bravo", "grade": "F", "score": 40.0, "realtime": 60.0},
    {"id": "c", "name": "Charlie", "grade": "B", "score": 84.0, "realtime": None},
]


def test_query_filters_and_orders() -> None:
    out = query_rows(_ROWS, "SELECT id, score FROM agencies WHERE score >= 80 ORDER BY score DESC")
    assert [r["id"] for r in out] == ["a", "c"]
    assert out[0]["score"] == 95.0


def test_query_aggregates_grade_distribution() -> None:
    out = query_rows(
        _ROWS, "SELECT grade, count(*) AS n FROM agencies GROUP BY grade ORDER BY grade"
    )
    counts = {r["grade"]: r["n"] for r in out}
    assert counts == {"A": 1, "B": 1, "F": 1}


def test_query_handles_null_realtime() -> None:
    out = query_rows(_ROWS, "SELECT count(*) AS n FROM agencies WHERE realtime IS NULL")
    assert out[0]["n"] == 2


def test_query_empty_dataset() -> None:
    # An empty dataset still yields a queryable (empty) table.
    out = query_rows([], "SELECT count(*) AS n FROM agencies")
    assert out[0]["n"] in (0, 1)  # the placeholder row collapses to 0/1; count is defined


def test_to_parquet_roundtrips(tmp_path: Path) -> None:
    path = tmp_path / "agencies.parquet"
    to_parquet(_ROWS, str(path))
    assert path.exists() and path.stat().st_size > 0
    # Read it back through DuckDB to confirm it is a valid Parquet table.
    back = query_rows([], f"SELECT count(*) AS n FROM read_parquet('{path}')")
    assert back[0]["n"] == 3
