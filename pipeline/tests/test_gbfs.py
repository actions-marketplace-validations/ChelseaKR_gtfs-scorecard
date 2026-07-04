"""Tests for the GBFS version-currency check (pure)."""

from __future__ import annotations

from scorecard_pipeline.gbfs import (
    CURRENT,
    OUTDATED,
    SUPPORTED,
    UNKNOWN,
    assess_catalog,
    parse_systems_csv,
    render_report,
    version_status,
)

_CSV = (
    "Country Code,Name,Location,System ID,Auto-Discovery URL,Supported Versions\n"
    "US,Bay Wheels,San Francisco CA,bay_wheels,https://x/gbfs.json,2.3;3.0\n"
    "US,Old Scoot,Davis CA,old_scoot,https://y/gbfs.json,1.1\n"
    "US,Mid Bikes,Sacramento CA,mid_bikes,https://z/gbfs.json,2.3\n"
    "FR,Velib,Paris,velib,https://p/gbfs.json,2.2\n"
    "US,Mystery,Nowhere,mystery,https://m/gbfs.json,\n"
    "US,No URL,Nowhere,no_url,,3.0\n"  # dropped: no discovery URL
)


def test_version_status_bands() -> None:
    assert version_status(("3.0",)) == CURRENT
    assert version_status(("2.3", "3.0")) == CURRENT  # highest wins
    assert version_status(("2.3",)) == SUPPORTED
    assert version_status(("2.2",)) == OUTDATED
    assert version_status(("1.1",)) == OUTDATED
    assert version_status(()) == UNKNOWN


def test_parse_drops_rows_without_discovery_url_and_reads_versions() -> None:
    systems = parse_systems_csv(_CSV)
    ids = {s.system_id for s in systems}
    assert "no_url" not in ids
    bay = next(s for s in systems if s.system_id == "bay_wheels")
    assert bay.supported_versions == ("2.3", "3.0")
    assert bay.country_code == "US"


def test_assess_catalog_counts_and_lists_outdated() -> None:
    summary = assess_catalog(parse_systems_csv(_CSV))
    assert summary.total == 5  # no_url dropped
    assert summary.current == 1  # bay_wheels
    assert summary.supported == 1  # mid_bikes
    assert summary.outdated == 2  # old_scoot, velib
    assert summary.unknown == 1  # mystery
    assert {s.system_id for s in summary.outdated_systems} == {"old_scoot", "velib"}
    # Outdated list is sorted by name.
    assert [s.name for s in summary.outdated_systems] == ["Old Scoot", "Velib"]


def test_render_report_headlines_currency_and_lists_outdated() -> None:
    report = render_report(assess_catalog(parse_systems_csv(_CSV)))
    assert "1 of 5 systems are on the current GBFS 3.x line" in report
    assert "Old Scoot" in report and "supports 1.1" in report


def test_render_report_empty() -> None:
    assert "No GBFS systems found" in render_report(assess_catalog([]), country="US")
