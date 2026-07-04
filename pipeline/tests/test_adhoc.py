"""The ad-hoc `scorecard try` path: score any feed without publishing it.

run_adhoc reuses the same fetch -> validate -> score chain as a tracked agency
but writes nothing to the public artifacts or index. These tests stub the
network and the Java validator so they run offline, and assert the artifact is
produced without touching artifacts_dir().
"""

from __future__ import annotations

import datetime as dt
import io
from contextlib import redirect_stdout
from pathlib import Path

from scorecard_pipeline import cli
from scorecard_pipeline.config import artifacts_dir
from scorecard_pipeline.fetch import FetchResult
from scorecard_pipeline.validate import NoticeGroup, ValidationReport

FIXTURE = Path(__file__).parent / "fixtures" / "unitrans_trimmed.zip"


def _stub_fetch(monkeypatch: object) -> None:
    fr = FetchResult(
        agency_id="_adhoc",
        path=FIXTURE,
        url="https://example.test/gtfs.zip",
        fetched_date=dt.date(2026, 6, 11),
        sha256="ab" * 32,
        size_bytes=FIXTURE.stat().st_size,
        reused=False,
    )
    report = ValidationReport(
        validator_version="9.9.9",
        notices=[NoticeGroup(code="route_short_name_too_long", severity="WARNING", total=2)],
    )
    monkeypatch.setattr(cli, "fetch_static", lambda *a, **k: fr)  # type: ignore[attr-defined]
    monkeypatch.setattr(cli, "run_validator", lambda *a, **k: Path("unused.json"))  # type: ignore[attr-defined]
    monkeypatch.setattr(cli, "parse_report", lambda *a, **k: report)  # type: ignore[attr-defined]


def test_run_adhoc_scores_without_publishing(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _stub_fetch(monkeypatch)
    artifact = cli.run_adhoc("https://example.test/gtfs.zip", "Test Agency", dt.date(2026, 6, 11))

    assert artifact["agency"]["name"] == "Test Agency"
    assert artifact["agency"]["id"] == "_adhoc"
    assert artifact["overall"]["grade"] in {"A", "B", "C", "D", "F"}
    # realtime is never sampled for an ad-hoc URL
    assert artifact["categories"]["realtime"]["status"] != "measured"
    # nothing was published to the public artifacts tree
    assert not (artifacts_dir() / "_adhoc").exists()


def test_run_adhoc_defaults_name_to_host(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _stub_fetch(monkeypatch)
    artifact = cli.run_adhoc("https://transit.example.org/feed.zip", None, dt.date(2026, 6, 11))
    assert artifact["agency"]["name"] == "transit.example.org"


def test_print_summary_includes_grade_and_fixes() -> None:
    artifact = {
        "agency": {"name": "Demo Transit"},
        "feed": {"static_url": "https://demo.test/gtfs.zip"},
        "overall": {"grade": "B", "score": 84.2},
        "categories": {
            "correctness": {"status": "measured", "score": 88.0},
            "freshness": {"status": "measured", "score": 75.0},
            "completeness": {"status": "measured", "score": 90.0},
            "realtime": {"status": "not_yet_measured"},
        },
        "top_fixes": [
            {"fix": "Re-export with a longer calendar window.", "effort": "One setting."}
        ],
    }
    buf = io.StringIO()
    with redirect_stdout(buf):
        cli._print_scorecard_summary(artifact)
    out = buf.getvalue()
    assert "Demo Transit" in out
    assert "Overall grade: B" in out
    assert "Rider experience" in out  # completeness relabeled
    assert "not yet measured" in out  # realtime
    assert "Re-export with a longer calendar window." in out
