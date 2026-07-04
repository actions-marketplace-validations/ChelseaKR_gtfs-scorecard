"""Tests for self-serve onboarding: issue parsing and comment rendering (pure)."""

from __future__ import annotations

from typing import Any

from scorecard_pipeline.onboard import parse_issue_form, render_comment

_FORM_BODY = """### GTFS Schedule URL

https://agency.example/google_transit.zip

### Agency name

Fairfield and Suisun Transit
"""

_FORM_NO_NAME = """### GTFS Schedule URL

https://agency.example/feed.zip

### Agency name

_No response_
"""


def test_parse_reads_url_and_name_from_form() -> None:
    req = parse_issue_form(_FORM_BODY)
    assert req is not None
    assert req.url == "https://agency.example/google_transit.zip"
    assert req.name == "Fairfield and Suisun Transit"


def test_parse_falls_back_to_generic_name() -> None:
    req = parse_issue_form(_FORM_NO_NAME)
    assert req is not None
    assert req.url == "https://agency.example/feed.zip"
    assert req.name == "this feed"


def test_parse_finds_url_in_free_text_without_the_form() -> None:
    req = parse_issue_form("Please grade https://x.example/gtfs.zip when you can, thanks.")
    assert req is not None
    assert req.url == "https://x.example/gtfs.zip"


def test_parse_strips_trailing_punctuation() -> None:
    req = parse_issue_form("### GTFS Schedule URL\n\n(https://x.example/feed.zip).")
    assert req is not None
    assert req.url == "https://x.example/feed.zip"


def test_parse_returns_none_without_a_url() -> None:
    assert parse_issue_form("### GTFS Schedule URL\n\n_No response_") is None
    assert parse_issue_form("no link here") is None


def test_parse_ignores_non_http_schemes() -> None:
    assert parse_issue_form("ftp://x.example/feed.zip") is None


def test_parse_collapses_a_multiline_name_to_one_line() -> None:
    body = "### GTFS Schedule URL\n\nhttps://x.example/f.zip\n\n### Agency name\n\nDemo\nInjected"
    req = parse_issue_form(body)
    assert req is not None
    assert "\n" not in req.name
    assert req.name == "Demo Injected"


def _artifact() -> dict[str, Any]:
    return {
        "agency": {"name": "Fairfield and Suisun Transit"},
        "overall": {"grade": "B", "score": 84.2},
        "categories": {
            "correctness": {"status": "measured", "score": 90.0},
            "freshness": {"status": "measured", "score": 85.0},
            "completeness": {"status": "measured", "score": 78.0},
            "realtime": {"status": "not_yet_measured"},
        },
        "top_fixes": [
            {"fix": "Set wheelchair_boarding on every stop.", "effort": "A column in stops.txt."},
            {"fix": "Add a feed_contact_email.", "effort": "One field."},
        ],
    }


def test_render_comment_leads_with_grade_and_lists_fixes() -> None:
    md = render_comment(_artifact(), page_url="https://gtfsscorecard.org/x")
    assert "GTFS Scorecard: Fairfield and Suisun Transit" in md
    assert "**Grade B** (84.2/100)" in md
    assert "| Correctness | 90.0 |" in md
    assert "| Realtime | not yet published |" in md
    assert "Set wheelchair_boarding on every stop." in md
    assert "_A column in stops.txt._" in md
    assert "https://gtfsscorecard.org/x" in md
    assert "add your agency" in md.lower()


def test_render_comment_handles_no_fixes() -> None:
    art = _artifact()
    art["top_fixes"] = []
    md = render_comment(art)
    assert "No score-moving fixes stood out" in md
