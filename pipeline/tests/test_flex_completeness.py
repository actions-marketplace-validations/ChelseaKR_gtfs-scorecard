"""Tests for GTFS-Flex completeness scoring (built on detect_flex, ADR 0007)."""

from __future__ import annotations

from scorecard_pipeline.flex import (
    FlexProfile,
    flex_completeness,
    flex_completeness_findings,
)


def _full_flex() -> FlexProfile:
    return FlexProfile(
        has_flex=True,
        has_booking_rules=True,
        booking_reachable=True,
        booking_rule_count=1,
    )


def test_full_flex_feed_scores_high() -> None:
    result = flex_completeness(_full_flex())
    assert result.present is True
    assert result.score == 100.0
    assert all(v == 1.0 for v in result.components.values())
    assert flex_completeness_findings(_full_flex()) == []


def test_flex_missing_booking_rules_scores_lower_with_finding() -> None:
    profile = FlexProfile(
        has_flex=True,
        has_booking_rules=False,
        booking_reachable=False,
        booking_rule_count=0,
    )
    result = flex_completeness(profile)
    assert result.present is True
    assert result.score < 100.0
    assert result.components["service_zones"] == 1.0
    assert result.components["booking_rules"] == 0.0
    assert any("no booking_rules.txt" in note for note in result.notes)

    (finding,) = flex_completeness_findings(profile)
    assert finding.code == "scorecard_flex_completeness_no_booking_rules"
    assert finding.severity == "WARNING"
    assert finding.deduction == 0.0


def test_flex_booking_present_but_unreachable_has_contact_finding() -> None:
    profile = FlexProfile(
        has_flex=True,
        has_booking_rules=True,
        booking_reachable=False,
        booking_rule_count=2,
    )
    result = flex_completeness(profile)
    assert result.present is True
    assert result.components["booking_rules"] == 1.0
    assert result.components["booking_reachable"] == 0.0
    assert result.score < 100.0

    (finding,) = flex_completeness_findings(profile)
    assert finding.code == "scorecard_flex_completeness_no_contact"
    assert finding.count == 2
    assert finding.deduction == 0.0


def test_non_flex_feed_is_neutral() -> None:
    profile = FlexProfile(
        has_flex=False,
        has_booking_rules=False,
        booking_reachable=False,
        booking_rule_count=0,
    )
    result = flex_completeness(profile)
    assert result.present is False
    assert result.score == 0.0
    assert result.components == {}
    assert result.notes  # carries a neutral, non-applicable note
    assert flex_completeness_findings(profile) == []


def test_to_details_is_json_friendly() -> None:
    details = flex_completeness(_full_flex()).to_details()
    assert details["present"] is True
    assert details["score"] == 100.0
    assert set(details["components"]) == {
        "service_zones",
        "booking_rules",
        "booking_reachable",
        "booking_contact",
    }
    assert isinstance(details["notes"], list)
