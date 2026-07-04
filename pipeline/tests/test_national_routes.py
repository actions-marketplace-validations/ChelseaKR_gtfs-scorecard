"""Tests for the national all-routes aggregation (pure, filesystem-only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scorecard_pipeline.national_routes import (
    build_national_routes,
    feature_collection,
    load_catalog_grades,
    write_geojsonl,
)


def _route_feature(route_id: str, label: str, type_label: str) -> dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": [[-121.7, 38.5], [-121.6, 38.6]]},
        "properties": {
            "kind": "route",
            "route_id": route_id,
            "label": label,
            "long": f"{label} long name",
            "type_label": type_label,
            "color": "#1A7A46",
            "color_name": "green",
        },
    }


def _stop_feature(stop_id: str) -> dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-121.7, 38.5]},
        "properties": {"kind": "stop", "stop_id": stop_id, "name": f"Stop {stop_id}"},
    }


def _write_geometry(agency_dir: Path, features: list[dict[str, Any]]) -> None:
    agency_dir.mkdir(parents=True, exist_ok=True)
    (agency_dir / "geometry.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features})
    )


def _artifacts(tmp_path: Path) -> Path:
    art = tmp_path / "artifacts"
    _write_geometry(
        art / "alpha",
        [_route_feature("A", "A", "Bus"), _stop_feature("s1"), _route_feature("B", "B", "Rail")],
    )
    _write_geometry(art / "beta", [_route_feature("R", "Red", "Tram / light rail")])
    return art


def test_aggregation_keeps_only_routes_and_tags_them(tmp_path: Path) -> None:
    art = _artifacts(tmp_path)
    grades = {
        "alpha": {"name": "Alpha Transit", "grade": "B"},
        "beta": {"name": "Beta Transit", "grade": "A"},
    }
    result = build_national_routes(art, grades)

    # Three route lines total; the stop point is dropped.
    assert result.summary["route_count"] == 3
    assert result.summary["agency_count"] == 2
    kinds = {f["geometry"]["type"] for f in result.features}
    assert kinds == {"LineString"}

    # Each feature carries the agency, name, route, type, and grade.
    alpha_a = next(
        f
        for f in result.features
        if f["properties"]["agency"] == "alpha" and f["properties"]["route"] == "A"
    )
    assert alpha_a["properties"]["agency_name"] == "Alpha Transit"
    assert alpha_a["properties"]["type"] == "Bus"
    assert alpha_a["properties"]["grade"] == "B"


def test_summary_counts_by_grade_and_type(tmp_path: Path) -> None:
    art = _artifacts(tmp_path)
    grades = {
        "alpha": {"name": "Alpha Transit", "grade": "B"},
        "beta": {"name": "Beta Transit", "grade": "A"},
    }
    result = build_national_routes(art, grades)
    assert result.summary["grade_counts"] == {"A": 1, "B": 2}
    assert result.summary["type_counts"] == {"Bus": 1, "Rail": 1, "Tram / light rail": 1}


def test_missing_grade_falls_back_to_unknown(tmp_path: Path) -> None:
    art = _artifacts(tmp_path)
    result = build_national_routes(art, {})  # no catalog grades at all
    for feature in result.features:
        assert feature["properties"]["grade"] == "?"
        # Name falls back to the agency id when the catalog has no entry.
        assert feature["properties"]["agency_name"] == feature["properties"]["agency"]


def test_deterministic_ordering(tmp_path: Path) -> None:
    art = _artifacts(tmp_path)
    first = build_national_routes(art, {}).features
    second = build_national_routes(art, {}).features
    assert first == second
    # Agencies in id order: all alpha routes precede beta.
    agencies = [f["properties"]["agency"] for f in first]
    assert agencies == sorted(agencies)


def test_unreadable_or_missing_geometry_is_skipped(tmp_path: Path) -> None:
    art = tmp_path / "artifacts"
    _write_geometry(art / "good", [_route_feature("A", "A", "Bus")])
    # An agency dir with no geometry file, and one with malformed JSON.
    (art / "nogeo").mkdir(parents=True)
    bad = art / "broken"
    bad.mkdir(parents=True)
    (bad / "geometry.geojson").write_text("{ not json")
    result = build_national_routes(art, {})
    assert result.summary["route_count"] == 1
    assert result.summary["agency_count"] == 1


def test_write_geojsonl_one_feature_per_line(tmp_path: Path) -> None:
    art = _artifacts(tmp_path)
    routes = build_national_routes(art, {})
    out = tmp_path / "out" / "national.geojsonl"
    count = write_geojsonl(routes, out)
    lines = out.read_text().splitlines()
    assert count == 3
    assert len(lines) == 3
    for line in lines:
        obj = json.loads(line)
        assert obj["type"] == "Feature"
        assert obj["geometry"]["type"] == "LineString"


def test_feature_collection_wraps_features(tmp_path: Path) -> None:
    art = _artifacts(tmp_path)
    routes = build_national_routes(art, {})
    fc = feature_collection(routes)
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 3


def test_load_catalog_grades(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "agencies": [
                    {"id": "alpha", "name": "Alpha Transit", "grade": "B"},
                    {"id": "beta", "name": "Beta Transit", "grade": "A"},
                    {"name": "no id, skipped"},
                ]
            }
        )
    )
    grades = load_catalog_grades(catalog)
    assert grades == {
        "alpha": {"name": "Alpha Transit", "grade": "B"},
        "beta": {"name": "Beta Transit", "grade": "A"},
    }


def test_load_catalog_grades_missing_file(tmp_path: Path) -> None:
    assert load_catalog_grades(tmp_path / "absent.json") == {}
