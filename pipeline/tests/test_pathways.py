"""Tests for station pathways and levels detection (ADR 0009)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from scorecard_pipeline.gtfs import read_tables
from scorecard_pipeline.pathways import PathwaysProfile, detect_pathways, pathways_findings

FLAT_STOPS = "stop_id,stop_name,location_type\nS1,Main St,0\nS2,2nd Ave,\n"
STATION_STOPS = (
    "stop_id,stop_name,location_type,parent_station\n"
    "STA,Transit Center,1,\n"
    "E1,North Entrance,2,STA\n"
    "P1,Platform 1,0,STA\n"
)


def _profile(make_gtfs_zip: Callable[..., Path], files: dict[str, str]) -> PathwaysProfile:
    path = make_gtfs_zip({"agency.txt": "agency_id,agency_name\nx,X\n", **files})
    stops = read_tables(str(path), ["stops.txt"])["stops.txt"]
    return detect_pathways(str(path), stops)


def test_flat_stop_only_feed_is_not_flagged(make_gtfs_zip: Callable[..., Path]) -> None:
    profile = _profile(make_gtfs_zip, {"stops.txt": FLAT_STOPS})
    assert profile.models_stations is False
    assert pathways_findings(profile) == []


def test_station_without_pathways_is_flagged(make_gtfs_zip: Callable[..., Path]) -> None:
    profile = _profile(make_gtfs_zip, {"stops.txt": STATION_STOPS})
    assert profile.has_stations is True
    assert profile.has_entrances is True
    assert profile.has_pathways is False
    (finding,) = pathways_findings(profile)
    assert finding.code == "scorecard_station_no_pathways"
    assert finding.deduction == 0.0


def test_station_with_step_free_pathways_is_acknowledged(
    make_gtfs_zip: Callable[..., Path],
) -> None:
    files = {
        "stops.txt": STATION_STOPS,
        "levels.txt": "level_id,level_index,level_name\nL0,0,Street\nL1,1,Platform\n",
        "pathways.txt": (
            "pathway_id,from_stop_id,to_stop_id,pathway_mode,is_bidirectional\n"
            "PW1,E1,P1,5,1\n"  # mode 5 = elevator, a step-free route
        ),
    }
    profile = _profile(make_gtfs_zip, files)
    assert profile.has_pathways is True
    assert profile.has_levels is True
    assert profile.has_step_free is True
    (note,) = pathways_findings(profile)
    assert note.code == "scorecard_station_pathways"
    assert "step-free" in note.what
    assert note.deduction == 0.0


def test_pathways_without_elevator_notes_the_missing_step_free_route(
    make_gtfs_zip: Callable[..., Path],
) -> None:
    files = {
        "stops.txt": STATION_STOPS,
        "pathways.txt": (
            "pathway_id,from_stop_id,to_stop_id,pathway_mode,is_bidirectional\n"
            "PW1,E1,P1,2,1\n"  # mode 2 = stairs only
        ),
    }
    profile = _profile(make_gtfs_zip, files)
    assert profile.has_pathways is True
    assert profile.has_step_free is False
    (note,) = pathways_findings(profile)
    assert note.code == "scorecard_station_pathways"
    assert "elevator" in note.fix
