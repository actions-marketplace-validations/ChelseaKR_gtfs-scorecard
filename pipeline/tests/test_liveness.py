"""Tests for cheap feed change/liveness detection (injected opener, no network)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request

from scorecard_pipeline.liveness import (
    CHANGED,
    UNCHANGED,
    UNREACHABLE,
    LivenessRecord,
    check_feed,
    conditional_headers,
    load_state,
    recovered,
    save_state,
)

URL = "https://feeds.example.org/gtfs.zip"


class _FakeResp:
    def __init__(self, body: bytes, headers: dict[str, str]) -> None:
        self.status = 200
        self._body = body
        self.headers = headers

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def _opener_returning(
    body: bytes, headers: dict[str, str] | None = None
) -> Callable[[Request, float], _FakeResp]:
    def opener(req: Request, timeout: float) -> _FakeResp:
        return _FakeResp(body, headers or {})

    return opener


def _opener_raising(exc: Exception) -> Callable[[Request, float], _FakeResp]:
    def opener(req: Request, timeout: float) -> _FakeResp:
        raise exc

    return opener


def _opener_read_raises(exc: Exception) -> Callable[[Request, float], _FakeResp]:
    """Opener that connects fine but whose body read fails mid-download."""

    class _BrokenResp(_FakeResp):
        def read(self) -> bytes:
            raise exc

    def opener(req: Request, timeout: float) -> _FakeResp:
        return _BrokenResp(b"", {})

    return opener


def _rec(body: bytes, **kw: object) -> LivenessRecord:
    return LivenessRecord(url=URL, sha256=hashlib.sha256(body).hexdigest(), **kw)  # type: ignore[arg-type]


def test_conditional_headers_use_stored_validators() -> None:
    prev = LivenessRecord(url=URL, etag='"abc"', last_modified="Wed, 21 Oct 2026 07:28:00 GMT")
    h = conditional_headers(prev)
    assert h["If-None-Match"] == '"abc"'
    assert h["If-Modified-Since"] == "Wed, 21 Oct 2026 07:28:00 GMT"
    assert "User-Agent" in h
    # No prior record: only the user agent, no conditional validators.
    assert set(conditional_headers(None)) == {"User-Agent"}


def test_304_is_unchanged_and_clears_failures() -> None:
    prev = _rec(b"old", consecutive_failures=2)
    err = HTTPError(URL, 304, "Not Modified", {}, None)  # type: ignore[arg-type]
    rec, cls = check_feed(URL, prev, opener=_opener_raising(err), now="2026-06-20T00:00:00+00:00")
    assert cls == UNCHANGED
    assert rec.sha256 == prev.sha256  # carried forward
    assert rec.status == 304
    assert rec.consecutive_failures == 0


def test_200_with_new_body_is_changed() -> None:
    prev = _rec(b"old")
    opener = _opener_returning(b"new feed bytes", {"ETag": '"v2"'})
    rec, cls = check_feed(URL, prev, opener=opener, now="2026-06-20T00:00:00+00:00")
    assert cls == CHANGED
    assert rec.sha256 == hashlib.sha256(b"new feed bytes").hexdigest()
    assert rec.etag == '"v2"'
    assert rec.changed_at == "2026-06-20T00:00:00+00:00"


def test_200_with_same_body_is_unchanged_even_without_304() -> None:
    # A host that ignores conditional headers and re-sends the same bytes is still
    # unchanged; the body hash is authoritative.
    body = b"identical feed"
    prev = _rec(body, changed_at="2026-06-01T00:00:00+00:00")
    rec, cls = check_feed(
        URL, prev, opener=_opener_returning(body), now="2026-06-20T00:00:00+00:00"
    )
    assert cls == UNCHANGED
    assert rec.changed_at == "2026-06-01T00:00:00+00:00"  # unchanged keeps the old change time


def test_first_check_with_no_prior_record_is_changed() -> None:
    rec, cls = check_feed(URL, None, opener=_opener_returning(b"first"))
    assert cls == CHANGED
    assert rec.sha256 == hashlib.sha256(b"first").hexdigest()


def test_http_error_is_unreachable_and_counts_failures() -> None:
    prev = _rec(b"old", consecutive_failures=1)
    err = HTTPError(URL, 403, "Forbidden", {}, None)  # type: ignore[arg-type]
    rec, cls = check_feed(URL, prev, opener=_opener_raising(err))
    assert cls == UNREACHABLE
    assert rec.status == 403
    assert rec.consecutive_failures == 2
    assert rec.sha256 == prev.sha256  # last known hash preserved


def test_url_error_is_unreachable() -> None:
    rec, cls = check_feed(URL, None, opener=_opener_raising(URLError("dns")))
    assert cls == UNREACHABLE
    assert rec.consecutive_failures == 1
    assert rec.status is None


def test_connection_reset_during_read_is_unreachable() -> None:
    # The connection opens but the server drops it mid-download (the real failure
    # the daily sweep hit). It must classify unreachable, not crash the sweep.
    prev = _rec(b"old", consecutive_failures=0)
    rec, cls = check_feed(
        URL,
        prev,
        opener=_opener_read_raises(ConnectionResetError(104, "reset by peer")),
        now="2026-06-20T00:00:00+00:00",
    )
    assert cls == UNREACHABLE
    assert rec.consecutive_failures == 1
    assert rec.sha256 == prev.sha256  # last known hash preserved


def test_recovered_flags_a_previously_failing_feed() -> None:
    failing = _rec(b"x", consecutive_failures=3)
    assert recovered(failing, UNCHANGED) is True
    assert recovered(failing, UNREACHABLE) is False
    assert recovered(None, CHANGED) is False
    assert recovered(_rec(b"x", consecutive_failures=0), CHANGED) is False


def test_state_round_trips_through_disk(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "liveness.json"
    state = {
        "demo": _rec(b"a", etag='"e"', status=200, checked_at="2026-06-20T00:00:00+00:00"),
        "other": LivenessRecord(url="https://x/y.zip", status=403, consecutive_failures=4),
    }
    save_state(path, state)
    back = load_state(path)
    assert back["demo"].sha256 == state["demo"].sha256
    assert back["demo"].etag == '"e"'
    assert back["other"].consecutive_failures == 4
    # Missing file degrades to empty, not an error.
    assert load_state(tmp_path / "nope.json") == {}
