"""Tests for the NTD-ID crosswalk (ntd_crosswalk.py)."""

from __future__ import annotations

from typing import Any

from scorecard_pipeline.ntd_crosswalk import (
    Proposal,
    agencies_with_ntd_id,
    apply_to_yaml,
    build_index,
    fetch_atlas,
    match_agencies,
    normalize_url,
)


def test_normalize_url_scheme_and_trailing_slash() -> None:
    a = normalize_url("https://Example.ORG/gtfs/feed.zip/")
    b = normalize_url("http://www.example.org/gtfs/feed.zip")
    assert a == b == "example.org/gtfs/feed.zip"


def test_normalize_url_keeps_query() -> None:
    # Operator is distinguished only by the query string; it must survive.
    assert normalize_url("http://api.511.org/transit/datafeeds?operator_id=SM") == (
        "api.511.org/transit/datafeeds?operator_id=SM"
    )


def _doc() -> dict[str, Any]:
    return {
        "feeds": [
            {"id": "f-aaa", "urls": {"static_current": "https://a.org/gtfs.zip"}},
            {"id": "f-bbb", "urls": {"static_current": "https://b.org/gtfs.zip"}},
            {"id": "f-shared", "urls": {"static_current": "https://region.org/gtfs.zip"}},
        ],
        "operators": [
            {
                "tags": {"us_ntd_id": "90001"},
                "associated_feeds": [
                    {"feed_onestop_id": "f-aaa"},
                    {"feed_onestop_id": "f-shared"},
                ],
            },
            {
                "tags": {"us_ntd_id": "90002"},
                "associated_feeds": [
                    {"feed_onestop_id": "f-bbb"},
                    {"feed_onestop_id": "f-shared"},
                ],
            },
            {"tags": {}, "associated_feeds": [{"feed_onestop_id": "f-aaa"}]},
        ],
    }


def test_build_index_maps_url_to_ntd_and_drops_shared() -> None:
    index = build_index([_doc()])
    assert index["a.org/gtfs.zip"] == "90001"
    assert index["b.org/gtfs.zip"] == "90002"
    # The regional feed is linked to two NTD IDs, so it is dropped, not guessed.
    assert "region.org/gtfs.zip" not in index


def test_build_index_rejects_multivalue_and_nonnumeric_ntd() -> None:
    doc = {
        "feeds": [
            {"id": "f-multi", "urls": {"static_current": "https://m.org/g.zip"}},
            {"id": "f-bad", "urls": {"static_current": "https://bad.org/g.zip"}},
            {"id": "f-ok", "urls": {"static_current": "https://ok.org/g.zip"}},
        ],
        "operators": [
            # Comma-joined list: ambiguous for one feed, must be dropped.
            {
                "tags": {"us_ntd_id": "20113,20967"},
                "associated_feeds": [{"feed_onestop_id": "f-multi"}],
            },
            # Non-numeric junk: dropped.
            {"tags": {"us_ntd_id": "n/a"}, "associated_feeds": [{"feed_onestop_id": "f-bad"}]},
            # Clean single id: kept.
            {"tags": {"us_ntd_id": "90036"}, "associated_feeds": [{"feed_onestop_id": "f-ok"}]},
        ],
    }
    index = build_index([doc])
    assert index == {"ok.org/g.zip": "90036"}


def test_build_index_resolves_cross_document_feed_refs() -> None:
    # Operator and its feed live in different files; the index still links them.
    feed_doc = {"feeds": [{"id": "f-xyz", "urls": {"static_current": "https://x.org/g.zip"}}]}
    op_doc = {
        "operators": [
            {"tags": {"us_ntd_id": "90042"}, "associated_feeds": [{"feed_onestop_id": "f-xyz"}]}
        ]
    }
    index = build_index([feed_doc, op_doc])
    assert index["x.org/g.zip"] == "90042"


def test_match_agencies_by_url_and_skip() -> None:
    index = {"a.org/gtfs.zip": "90001", "b.org/gtfs.zip": "90002"}
    agencies = [
        {"id": "aaa", "static_gtfs_url": "http://a.org/gtfs.zip/"},
        {"id": "bbb", "static_gtfs_url": "https://b.org/gtfs.zip"},
        {"id": "ccc", "static_gtfs_url": "https://c.org/none.zip"},
        {"id": "no-url"},
    ]
    props = match_agencies(agencies, index, skip_ids={"bbb"})
    assert props == [Proposal("aaa", "90001")]


def test_agencies_with_ntd_id() -> None:
    text = (
        "agencies:\n"
        '  - id: pilot\n    name: "P"\n    static_gtfs_url: "https://p/g.zip"\n'
        '    ntd_id: "90142"\n'
        '  - id: plain\n    name: "Q"\n    static_gtfs_url: "https://q/g.zip"\n'
    )
    assert agencies_with_ntd_id(text) == {"pilot"}


def test_apply_to_yaml_inserts_one_line_and_preserves_existing() -> None:
    text = (
        "agencies:\n"
        '  - id: pilot\n    name: "P"\n    static_gtfs_url: "https://p/g.zip"\n'
        '    ntd_id: "90142"\n'
        '  - id: plain\n    name: "Q"\n    static_gtfs_url: "https://q/g.zip"\n'
    )
    proposals = [Proposal("pilot", "99999"), Proposal("plain", "90002")]
    new_text, inserted = apply_to_yaml(text, proposals)
    assert inserted == 1
    # The curated pilot is untouched; the plain agency gains exactly one line.
    assert '    ntd_id: "90142"' in new_text
    assert '    ntd_id: "99999"' not in new_text
    lines = new_text.split("\n")
    i = lines.index("  - id: plain")
    assert lines[i + 1] == '    ntd_id: "90002"'
    # Round-trips as valid YAML with the new value.
    assert agencies_with_ntd_id(new_text) == {"pilot", "plain"}


def test_apply_to_yaml_noop_when_nothing_to_add() -> None:
    text = 'agencies:\n  - id: a\n    ntd_id: "90001"\n'
    new_text, inserted = apply_to_yaml(text, [Proposal("a", "90001")])
    assert inserted == 0
    assert new_text == text


def test_fetch_atlas_uses_injected_fetch_and_skips_bad_files() -> None:
    listing = '[{"name": "good.dmfr.json"}, {"name": "bad.dmfr.json"}, {"name": "README.md"}]'
    bodies = {
        "good.dmfr.json": '{"feeds": [{"id": "f-1", "urls": {"static_current": "https://g/x"}}]}',
        "bad.dmfr.json": "{ not json",
    }

    def fake_fetch(url: str) -> str:
        if url.endswith("contents/feeds?ref=main"):
            return listing
        name = url.rsplit("/", 1)[-1]
        return bodies[name]

    docs = fetch_atlas(fake_fetch)
    assert len(docs) == 1
    assert docs[0]["feeds"][0]["id"] == "f-1"


# --- Name fallback ---------------------------------------------------------

from scorecard_pipeline.ntd_crosswalk import (  # noqa: E402
    build_name_index,
    match_agencies_by_name,
    normalize_name,
    operator_centroid,
)


def test_normalize_name_drops_boilerplate_and_sorts() -> None:
    a = normalize_name("Yolo County Transportation District")
    b = normalize_name("yolo  transportation (YCTD)")
    assert a == b == "yolo"
    # A name that is only boilerplate normalizes to empty (never matches).
    assert normalize_name("Regional Transit Authority") == ""


def test_operator_centroid_decodes_geohash() -> None:
    centroid = operator_centroid("o-9q8-samtrans")
    assert centroid is not None
    lat, lon = centroid
    # 9q8 is the San Francisco Bay Area.
    assert 36.0 < lat < 39.0
    assert -124.0 < lon < -121.0
    assert operator_centroid("noseg") is None


def _op(name: str, ntd: str, osid: str, short: str = "") -> dict[str, Any]:
    return {
        "operators": [
            {
                "name": name,
                "short_name": short,
                "onestop_id": osid,
                "tags": {"us_ntd_id": ntd},
            }
        ]
    }


def test_build_name_index_drops_globally_ambiguous_names() -> None:
    docs = [
        _op("Metro Transit", "11111", "o-9q8-a"),
        _op("Metro Transit", "22222", "o-dr5-b"),  # same name, different NTD -> dropped
        _op("Unitrans", "90142", "o-9qc-unitrans"),
    ]
    idx = build_name_index(docs)
    assert "metro" not in idx  # "transit" is boilerplate; "metro" alone is ambiguous
    assert idx["unitrans"]["ntd_id"] == "90142"


def test_match_by_name_requires_unique_name() -> None:
    idx = build_name_index([_op("Unitrans", "90142", "o-9qc-unitrans")])
    agencies: list[dict[str, Any]] = [
        {
            "id": "unitrans",
            "name": "Unitrans (ASUCD / City of Davis)",
            "lat": 38.55,
            "lon": -121.74,
        },
        {"id": "other", "name": "Some Other Transit Authority"},
    ]
    props = match_agencies_by_name(agencies, idx)
    assert props == [Proposal("unitrans", "90142")]


def test_match_by_name_geo_guardrail_rejects_far_coincidence() -> None:
    # Operator centroid is in the Bay Area; an agency of the same name on the east
    # coast is a name coincidence and must be rejected.
    idx = build_name_index([_op("Riverside Transit", "33333", "o-9q5-riverside")])
    agencies = [{"id": "east", "name": "Riverside Transit", "lat": 40.7, "lon": -74.0}]
    assert match_agencies_by_name(agencies, idx) == []


def test_match_by_name_accepts_when_geo_unknown() -> None:
    idx = build_name_index([_op("Unitrans", "90142", "o-9qc-unitrans")])
    agencies = [{"id": "unitrans", "name": "Unitrans"}]  # no lat/lon
    assert match_agencies_by_name(agencies, idx) == [Proposal("unitrans", "90142")]


def test_match_by_name_respects_skip_ids() -> None:
    idx = build_name_index([_op("Unitrans", "90142", "o-9qc-unitrans")])
    agencies = [{"id": "unitrans", "name": "Unitrans"}]
    assert match_agencies_by_name(agencies, idx, skip_ids={"unitrans"}) == []


def test_build_name_index_rejects_multivalue_and_nonnumeric_ntd() -> None:
    # A parent operating several subsidiaries carries a comma-joined us_ntd_id;
    # it must not be indexed as one malformed id (regression: RGRTA).
    docs = [
        _op("Rochester Genesee Regional", "20113,20967,20980", "o-dr9-rgrta"),
        _op("Bad Tag Agency", "not-a-number", "o-dr9-bad"),
        _op("Clean Agency", "40108", "o-dnq-clean"),
    ]
    idx = build_name_index(docs)
    assert "rochester genesee" not in idx
    assert "bad tag" not in idx  # "agency" is boilerplate
    assert idx["clean"]["ntd_id"] == "40108"
