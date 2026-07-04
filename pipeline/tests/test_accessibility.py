"""Tests for the accessibility-data deepening checks.

Each per-check function is tested directly with small fabricated row lists, so
no real zip is needed.
"""

from __future__ import annotations

from scorecard_pipeline.accessibility import (
    WCAG_AA_CONTRAST_RATIO,
    _contrast_ratio,
    pathway_sufficiency_findings,
    route_color_contrast_findings,
    tts_stop_name_findings,
)


def test_contrast_ratio_black_on_white_is_maximal() -> None:
    ratio = _contrast_ratio("FFFFFF", "000000")
    assert ratio is not None
    assert round(ratio, 1) == 21.0


def test_contrast_ratio_invalid_color_is_none() -> None:
    assert _contrast_ratio("FFFFFF", "ZZZ") is None
    assert _contrast_ratio("FFF", "000000") is None


def test_low_contrast_route_is_flagged() -> None:
    # Light gray fill with white text: well under 4.5:1.
    rows = [
        {
            "route_id": "R1",
            "route_short_name": "1",
            "route_color": "CCCCCC",
            "route_text_color": "FFFFFF",
        }
    ]
    (finding,) = route_color_contrast_findings(rows)
    assert finding.code == "scorecard_route_color_low_contrast"
    assert finding.count == 1
    assert "1" in finding.what
    assert finding.deduction == 0.0


def test_high_contrast_route_is_not_flagged() -> None:
    # Dark navy fill with white text: comfortably above 4.5:1.
    rows = [
        {
            "route_id": "R2",
            "route_short_name": "2",
            "route_color": "003366",
            "route_text_color": "FFFFFF",
        }
    ]
    assert route_color_contrast_findings(rows) == []


def test_route_with_no_colors_set_is_not_flagged() -> None:
    # A feed that omits route colors takes the GTFS default (black on white),
    # which passes, and is not the agency's own choice to flag.
    rows = [{"route_id": "R3", "route_short_name": "3", "route_color": "", "route_text_color": ""}]
    assert route_color_contrast_findings(rows) == []


def test_low_contrast_threshold_constant_is_wcag_aa() -> None:
    assert WCAG_AA_CONTRAST_RATIO == 4.5


def test_shouty_stop_name_without_tts_is_flagged() -> None:
    rows = [{"stop_id": "S1", "stop_name": "Main St & 2nd Ave", "tts_stop_name": ""}]
    (finding,) = tts_stop_name_findings(rows)
    assert finding.code == "scorecard_stop_name_needs_tts"
    assert finding.count == 1
    assert "Main St & 2nd Ave" in finding.what
    assert finding.deduction == 0.0


def test_stop_name_with_tts_override_is_not_flagged() -> None:
    rows = [
        {
            "stop_id": "S1",
            "stop_name": "Main St & 2nd Ave",
            "tts_stop_name": "Main Street and Second Avenue",
        }
    ]
    assert tts_stop_name_findings(rows) == []


def test_plain_stop_name_is_not_flagged() -> None:
    rows = [{"stop_id": "S2", "stop_name": "Memorial Union", "tts_stop_name": ""}]
    assert tts_stop_name_findings(rows) == []


def test_spelled_out_abbreviation_words_are_not_flagged() -> None:
    # "Saint" and "Avenue" spelled out should not match the abbreviation list.
    rows = [{"stop_id": "S3", "stop_name": "Saint Marys Avenue", "tts_stop_name": ""}]
    assert tts_stop_name_findings(rows) == []


def test_flat_feed_with_no_stations_produces_no_pathway_finding() -> None:
    stops = [
        {"stop_id": "S1", "stop_name": "Main St", "location_type": "0"},
        {"stop_id": "S2", "stop_name": "Second Ave", "location_type": ""},
    ]
    assert pathway_sufficiency_findings(stops, [], []) == []


def test_station_feed_missing_pathways_is_flagged() -> None:
    stops = [
        {"stop_id": "STA", "stop_name": "Transit Center", "location_type": "1"},
        {"stop_id": "E1", "stop_name": "North Entrance", "location_type": "2"},
        {"stop_id": "P1", "stop_name": "Platform 1", "location_type": "0"},
    ]
    (finding,) = pathway_sufficiency_findings(stops, [], [])
    assert finding.code == "scorecard_station_missing_step_free_data"
    assert "pathways.txt" in finding.what
    assert "levels.txt" in finding.what
    assert finding.count == 2
    assert finding.deduction == 0.0


def test_station_feed_with_pathways_and_levels_is_not_flagged() -> None:
    stops = [
        {"stop_id": "STA", "stop_name": "Transit Center", "location_type": "1"},
        {"stop_id": "P1", "stop_name": "Platform 1", "location_type": "0"},
    ]
    pathways = [
        {"pathway_id": "PW1", "from_stop_id": "STA", "to_stop_id": "P1", "pathway_mode": "5"}
    ]
    levels = [{"level_id": "L0", "level_index": "0"}]
    assert pathway_sufficiency_findings(stops, pathways, levels) == []


def test_station_feed_missing_only_levels_is_flagged_once() -> None:
    stops = [{"stop_id": "STA", "stop_name": "Transit Center", "location_type": "1"}]
    pathways = [
        {"pathway_id": "PW1", "from_stop_id": "STA", "to_stop_id": "STA", "pathway_mode": "1"}
    ]
    (finding,) = pathway_sufficiency_findings(stops, pathways, [])
    assert "levels.txt" in finding.what
    assert "pathways.txt" not in finding.what
    assert finding.count == 1
