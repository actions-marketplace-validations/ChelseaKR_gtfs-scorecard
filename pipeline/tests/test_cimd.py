"""Tests for the Canada CIMD equity data-assembly + methodology core (cimd.py).

The network fetch and CLI are the wiring step (ADR 0027), so these cover the pure
parsers, the join, and the served-area need tier against fixtures shaped like the
real CIMD CSV and StatCan DA-boundary GeoJSON.
"""

from __future__ import annotations

import pytest

from scorecard_pipeline.cimd import (
    CimdIndicators,
    _tier,
    build_das,
    parse_cimd,
    parse_cimd_features,
    parse_da_geometry,
    served_area_cimd,
    stops_bbox,
)

# CIMD CSV rows: header in a deliberately non-obvious order, with both a Scores
# column (must be ignored) and a quintile column per dimension.
_CIMD = [
    [
        "DAUID",
        "Economic dependency Scores",  # a score, not a quintile: must NOT match
        "Situational vulnerability Scores-Quintiles",
        "Economic dependency Scores-Quintiles",
        "Ethno-cultural composition Scores-Quintiles",
        "Residential instability Scores-Quintiles",
    ],
    ["48060123", "1.42", "5", "5", "1", "2"],  # high need (econ+sit both 5)
    ["48060124", "-0.3", "1", "1", "5", "5"],  # low need (econ+sit both 1)
    ["48060125", "0.0", "", "9", "3", "3"],  # sit blank, econ 9 out-of-range -> both None
]

# StatCan DA-boundary GeoJSON: one Polygon, one MultiPolygon (larger part wins),
# one unusable feature.
_GEO = {
    "type": "FeatureCollection",
    "features": [
        {
            "properties": {"DAUID": "48060123"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [0, 2], [2, 2], [2, 0], [0, 0]]],
            },
        },
        {
            "properties": {"DAUID": "48060124"},
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [[[10, 10], [10, 11], [11, 10], [10, 10]]],  # smaller
                    [[[10, 10], [10, 12], [12, 12], [12, 10], [10, 10]]],  # larger -> wins
                ],
            },
        },
        {"properties": {}, "geometry": None},  # skipped
    ],
}


def test_parse_cimd_matches_quintile_columns_by_keyword() -> None:
    cimd = parse_cimd(_CIMD)
    a = cimd["48060123"]
    # Quintile columns resolved regardless of order; the "Scores" column ignored.
    assert a.economic_dependency == 5 and a.situational_vulnerability == 5
    assert a.ethno_cultural_composition == 1 and a.residential_instability == 2
    b = cimd["48060124"]
    assert b.economic_dependency == 1 and b.situational_vulnerability == 1
    c = cimd["48060125"]
    assert c.situational_vulnerability is None  # blank -> None
    assert c.economic_dependency is None  # 9 is out of the 1-5 range -> None


def test_parse_da_geometry_polygon_and_multipolygon() -> None:
    geo = parse_da_geometry(_GEO)
    assert set(geo) == {"48060123", "48060124"}  # bad feature skipped
    # MultiPolygon reduced to its larger part (the 5-point ring).
    assert len(geo["48060124"][0]) == 5
    assert all(isinstance(x, float) and isinstance(y, float) for x, y in geo["48060123"][0])


def test_build_das_joins_and_drops_one_sided() -> None:
    geo = parse_da_geometry(_GEO)
    cimd = parse_cimd(_CIMD)
    cimd["99999999"] = CimdIndicators(economic_dependency=5)  # no geometry -> dropped
    das = build_das(geo, cimd)
    assert {d.dauid for d in das} == {"48060123", "48060124"}


def test_served_area_cimd_weights_and_tiers() -> None:
    das = build_das(parse_da_geometry(_GEO), parse_cimd(_CIMD))
    # Two stops in the high-need DA (around 0..2), one in the low-need DA (10..12).
    tier, mean_q = served_area_cimd([(1.0, 1.0), (1.5, 1.5), (11.0, 11.0)], das)
    assert mean_q == round((5 * 2 + 1 * 1) / 3, 2)  # stop-weighted
    assert tier == "moderate"  # 3.67 -> moderate
    # All service in the high-need DA -> high.
    assert served_area_cimd([(1.0, 1.0)], das)[0] == "high"
    # A stop in no DA is skipped; none served -> unknown.
    assert served_area_cimd([(50.0, 50.0)], das) == ("unknown", None)


def test_served_area_ignores_non_need_dimensions() -> None:
    # A DA that is low on the two need dimensions but high on ethno/residential
    # must read as low need: only economic + situational count (ADR 0027).
    geo = {"11111111": [[(0.0, 0.0), (0.0, 2.0), (2.0, 2.0), (2.0, 0.0), (0.0, 0.0)]]}
    cimd = {
        "11111111": CimdIndicators(
            economic_dependency=1,
            situational_vulnerability=1,
            ethno_cultural_composition=5,
            residential_instability=5,
        )
    }
    das = build_das(geo, cimd)
    assert served_area_cimd([(1.0, 1.0)], das) == ("lower", 1.0)


def test_tier_thresholds() -> None:
    assert _tier(None) == "unknown"
    assert _tier(5.0) == "high" and _tier(4.0) == "high"
    assert _tier(3.5) == "moderate" and _tier(3.0) == "moderate"
    assert _tier(2.9) == "lower" and _tier(1.0) == "lower"


def test_parse_cimd_uses_exact_dauid_not_adauid() -> None:
    # StatCan geography carries ADAUID (aggregate DA id) beside DAUID; a substring
    # match would key rows by the wrong id and silently drop every join.
    rows = [
        [
            "ADAUID",
            "DAUID",
            "Economic dependency Scores-Quintiles",
            "Situational vulnerability Scores-Quintiles",
        ],
        ["4806001", "48060123", "5", "4"],
    ]
    cimd = parse_cimd(rows)
    assert set(cimd) == {"48060123"}  # keyed by DAUID, not ADAUID
    assert cimd["48060123"].economic_dependency == 5


def test_parse_cimd_raises_on_unrecognized_header() -> None:
    # A header the keyword matcher can't resolve (e.g. a French export) must fail
    # loud, not silently score every DA "unknown".
    french = [["DAUID", "Dependance economique quintile"], ["48060123", "5"]]
    with pytest.raises(ValueError, match="not recognized"):
        parse_cimd(french)
    # Missing DAUID column also raises.
    with pytest.raises(ValueError, match="DAUID"):
        parse_cimd([["Economic dependency Scores-Quintiles"], ["5"]])


_CIMD_FEATURES = {
    "type": "FeatureCollection",
    "features": [
        {
            "properties": {
                "DAUID": "35390025",
                "Economic_dependency_Q": 3,  # ESRI returns quintiles as ints
                "Situational_vulnerability_Q": 1,
                "Residential_instability_Q": 2,
                "Ethno_cultural_composition_Q": None,  # null prop -> None
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [0, 2], [2, 2], [2, 0], [0, 0]]],
            },
        },
        {"properties": {"DAUID": ""}, "geometry": None},  # skipped
    ],
}


def test_parse_cimd_features_reads_geometry_and_quintiles() -> None:
    das = parse_cimd_features(_CIMD_FEATURES)
    assert len(das) == 1  # the DAUID-less/geometry-less feature is skipped
    d = das[0]
    assert d.dauid == "35390025"
    assert d.indicators.economic_dependency == 3
    assert d.indicators.situational_vulnerability == 1
    assert d.indicators.ethno_cultural_composition is None
    assert d.polygon[0][0] == (0.0, 0.0)  # geometry parsed alongside


def test_stops_bbox_pads_and_handles_empty() -> None:
    assert stops_bbox([]) is None
    bbox = stops_bbox([(-81.25, 42.98), (-81.20, 43.02)], pad=0.01)
    assert bbox == pytest.approx((-81.26, 42.97, -81.19, 43.03))


def test_served_area_single_need_dimension() -> None:
    # A DA with only one of the two need dimensions uses that one value.
    geo = {"22222222": [[(0.0, 0.0), (0.0, 2.0), (2.0, 2.0), (2.0, 0.0), (0.0, 0.0)]]}
    cimd = {"22222222": CimdIndicators(economic_dependency=4)}  # situational is None
    das = build_das(geo, cimd)
    assert served_area_cimd([(1.0, 1.0)], das) == ("high", 4.0)
