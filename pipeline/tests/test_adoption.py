"""Tests for the national GTFS-capability adoption rollup (adoption.py)."""

from __future__ import annotations

from typing import Any

from scorecard_pipeline.adoption import adoption_record, national_adoption


def _art(
    aid: str,
    name: str,
    state: str,
    *,
    measured: bool = True,
    fares: str = "none",
    flex: bool = False,
    pathways: bool = False,
    step_free: bool = False,
    no_details: bool = False,
) -> dict[str, Any]:
    comp: dict[str, Any] = {"status": "measured" if measured else "not_measured", "details": {}}
    if measured and not no_details:
        comp["details"] = {
            "fares": {"model": fares},
            "flex": {"has_flex": flex},
            "pathways": {"has_pathways": pathways, "has_step_free": step_free},
        }
    return {
        "agency": {"id": aid, "name": name, "state": state},
        "categories": {"completeness": comp},
    }


def test_record_extracts_capabilities() -> None:
    r = adoption_record(_art("a", "A", "CA", fares="v2", flex=True, pathways=True, step_free=True))
    assert r is not None
    assert r["has_flex"] and r["has_fares"] and r["has_fares_v2"]
    assert r["has_pathways"] and r["has_step_free"]
    assert r["fare_model"] == "v2" and r["state"] == "CA"


def test_record_skips_unmeasured_or_missing_details() -> None:
    assert adoption_record(_art("a", "A", "CA", measured=False)) is None
    assert adoption_record(_art("a", "A", "CA", no_details=True)) is None


def test_legacy_fares_is_not_v2() -> None:
    r = adoption_record(_art("a", "A", "CA", fares="legacy"))
    assert r is not None
    assert r["has_fares"] and not r["has_fares_v2"] and r["fare_model"] == "legacy"


def test_national_adoption_counts_shares_and_state_split() -> None:
    raw = [
        adoption_record(_art("a", "A", "CA", fares="v2", flex=True, pathways=True)),
        adoption_record(_art("b", "B", "CA", fares="legacy")),
        adoption_record(_art("c", "C", "NY")),  # publishes nothing new
        adoption_record(_art("d", "D", "", flex=True)),  # empty state -> Unlocated
    ]
    records: list[dict[str, Any]] = [r for r in raw if r is not None]
    nat = national_adoption(records, top=5)
    assert nat["agency_count"] == 4
    assert nat["flex"] == {"count": 2, "pct": 50.0}
    assert nat["fares"]["count"] == 2  # v2 + legacy
    assert nat["fares_v2"]["count"] == 1
    assert nat["pathways"]["count"] == 1
    assert nat["fare_models"] == {"none": 2, "legacy": 1, "v2": 1}
    ca = next(s for s in nat["states"] if s["state"] == "CA")
    assert ca["agencies"] == 2 and ca["flex"] == 1 and ca["fares"] == 2 and ca["fares_v2"] == 1
    assert any(s["state"] == "Unlocated" for s in nat["states"])
    assert {m["id"] for m in nat["flex_sample"]} == {"a", "d"}
    assert [m["id"] for m in nat["fares_v2_sample"]] == ["a"]


def test_empty_input() -> None:
    nat = national_adoption([])
    assert nat["agency_count"] == 0 and nat["flex"]["pct"] == 0.0
