"""Tests for producing-tool detection from the feed host (RESEARCH-ROADMAP R5)."""

from __future__ import annotations

from scorecard_pipeline.tool_profiles import KINDS, detect_tool


def test_trillium_detected_from_primary_host() -> None:
    tool = detect_tool("https://data.trilliumtransit.com/gtfs/unitrans-ca-us/unitrans.zip")
    assert tool is not None
    assert tool.key == "trillium"
    assert tool.kind == "hosted"
    assert "Trillium" in tool.fix_path


def test_trillium_detected_from_vendor_subdomain() -> None:
    tool = detect_tool("http://oregon-gtfs.trilliumtransit.com/some-or-us.zip")
    assert tool is not None and tool.key == "trillium"


def test_gtfs_builder_detected() -> None:
    tool = detect_tool("https://rapid.nationalrtap.org/Home/DownloadFile?id=123")
    assert tool is not None
    assert tool.key == "gtfs_builder"
    assert tool.kind == "self_edit"
    assert "GTFS Builder" in tool.fix_path


def test_repo_hosts_detected() -> None:
    for url in (
        "https://github.com/agency/gtfs/raw/main/gtfs.zip",
        "https://raw.githubusercontent.com/agency/gtfs/main/gtfs.zip",
        "https://gitlab.com/agency/gtfs/-/raw/main/gtfs.zip",
    ):
        tool = detect_tool(url)
        assert tool is not None and tool.key == "repo", url


def test_archive_host_detected() -> None:
    tool = detect_tool("https://transitfeeds.com/p/demo/1/latest/download")
    assert tool is not None
    assert tool.kind == "archive"
    assert "live URL" in tool.fix_path


def test_generic_hosting_stays_unmatched() -> None:
    # An S3 bucket or an agency's own site says nothing about the producing
    # tool; guessing would misdirect the one email a manager sends.
    for url in (
        "https://s3.amazonaws.com/bucket/gtfs.zip",
        "https://www.cityofdavis.org/files/gtfs.zip",
        "https://mjcaction.com/mjc_gtfs_public/demo/google_transit.zip",
    ):
        assert detect_tool(url) is None, url


def test_lookalike_host_is_not_a_suffix_match() -> None:
    # evil-github.com must not match github.com; only a dot boundary counts.
    assert detect_tool("https://nottransitfeeds.com/feed.zip") is None
    assert detect_tool("https://faketrilliumtransit.com/feed.zip") is None


def test_missing_or_blank_url_returns_none() -> None:
    assert detect_tool(None) is None
    assert detect_tool("") is None
    assert detect_tool("not a url") is None


def test_every_profile_kind_is_documented() -> None:
    # Each profile's kind must be one the render layer knows how to phrase.
    seen = set()
    for url in (
        "https://data.trilliumtransit.com/x.zip",
        "https://rapid.nationalrtap.org/x",
        "https://gtfs.remix.com/x.zip",
        "https://passio3.com/x/gtfs.zip",
        "https://github.com/x/x.zip",
        "https://transitfeeds.com/x",
    ):
        tool = detect_tool(url)
        assert tool is not None and tool.kind in KINDS
        seen.add(tool.kind)
    assert seen == set(KINDS)
