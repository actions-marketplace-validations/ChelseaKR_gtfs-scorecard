"""Unit tests for the serverless handler logic (infra/alerts, infra/submit).

These handlers are standalone Lambda modules outside the scorecard_pipeline
package, but their validation, token, and rate-limit logic is the most
security-sensitive code in the repo and was previously untested. They keep boto3
lazy, so the pure logic loads and runs without AWS; the few table-touching paths
are exercised with a fake table.
"""

from __future__ import annotations

import importlib.util
import time
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]


def _load(rel_path: str, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, REPO / rel_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


alerts = _load("infra/alerts/handler.py", "alerts_handler")
submit = _load("infra/submit/handler.py", "submit_handler")


class FakeTable:
    """Minimal stand-in for a DynamoDB Table."""

    def __init__(self, item: dict[str, Any] | None = None) -> None:
        self._item = item
        self.updated = False
        self.deleted = False

    def get_item(self, Key: dict[str, Any]) -> dict[str, Any]:  # noqa: N803 - boto3 kwarg name
        return {"Item": self._item} if self._item else {}

    def update_item(self, **_: Any) -> None:
        self.updated = True

    def delete_item(self, Key: dict[str, Any]) -> None:  # noqa: N803 - boto3 kwarg name
        self.deleted = True


# --- alerts: validate_subscribe ---


def test_validate_subscribe_normalizes_email_and_defaults_kinds() -> None:
    out = alerts.validate_subscribe({"email": "  Agency@Example.ORG ", "all": True})
    assert out["email"] == "agency@example.org"
    assert out["all"] is True
    assert out["kinds"] == ["expiry", "regression"]


def test_validate_subscribe_rejects_url_significant_email() -> None:
    for bad in ("a&b@x.io", "a?b@x.io", "a b@x.io", "nope"):
        with pytest.raises(alerts.BadRequest):
            alerts.validate_subscribe({"email": bad, "all": True})


def test_validate_subscribe_validates_agency_slugs_and_count() -> None:
    with pytest.raises(alerts.BadRequest):
        alerts.validate_subscribe({"email": "a@b.io", "agencies": ["Bad Slug!"]})
    with pytest.raises(alerts.BadRequest):
        alerts.validate_subscribe({"email": "a@b.io"})  # neither all nor agencies
    out = alerts.validate_subscribe({"email": "a@b.io", "agencies": ["unitrans", "yolobus"]})
    assert out["agencies"] == ["unitrans", "yolobus"]


def test_validate_subscribe_rejects_unknown_kind() -> None:
    with pytest.raises(alerts.BadRequest):
        alerts.validate_subscribe({"email": "a@b.io", "all": True, "kinds": ["nope"]})


# --- alerts: cooldown and secret gate ---


def test_email_on_cooldown() -> None:
    now = int(time.time())
    assert alerts._email_on_cooldown(None) is False
    assert alerts._email_on_cooldown({"verified": True, "requested_ts": now}) is False
    assert alerts._email_on_cooldown({"requested_ts": now}) is True
    assert alerts._email_on_cooldown({"requested_ts": now - 10_000}) is False


def test_secret_ok_open_when_unset_and_constant_time_when_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SUBSCRIBE_SHARED_SECRET", raising=False)
    assert alerts._secret_ok({}) is True
    monkeypatch.setenv("SUBSCRIBE_SHARED_SECRET", "s3cret")
    assert alerts._secret_ok({"headers": {"X-Subscribe-Token": "s3cret"}}) is True
    assert alerts._secret_ok({"headers": {"X-Subscribe-Token": "wrong"}}) is False
    assert alerts._secret_ok({}) is False


# --- alerts: confirm / unsubscribe token logic ---


def test_confirm_rejects_wrong_token_and_does_not_verify(monkeypatch: pytest.MonkeyPatch) -> None:
    table = FakeTable({"email": "a@b.io", "token": "good"})
    monkeypatch.setattr(alerts, "_table", lambda: table)
    resp = alerts._confirm({"rawQueryString": "email=a@b.io&token=wrong"})
    assert resp["statusCode"] == 400
    assert table.updated is False


def test_confirm_accepts_matching_token(monkeypatch: pytest.MonkeyPatch) -> None:
    table = FakeTable({"email": "a@b.io", "token": "good"})
    monkeypatch.setattr(alerts, "_table", lambda: table)
    resp = alerts._confirm({"rawQueryString": "email=a@b.io&token=good"})
    assert resp["statusCode"] == 200
    assert table.updated is True


def test_unsubscribe_missing_row_is_idempotent_success(monkeypatch: pytest.MonkeyPatch) -> None:
    table = FakeTable(None)
    monkeypatch.setattr(alerts, "_table", lambda: table)
    resp = alerts._unsubscribe({"rawQueryString": "email=a@b.io&token=x"})
    assert resp["statusCode"] == 200
    assert table.deleted is False


# --- submit: secret gate ---


def test_submit_options_preflight() -> None:
    resp = submit.handler({"requestContext": {"http": {"method": "OPTIONS"}}}, None)
    assert resp["statusCode"] == 204


def test_submit_rejects_wrong_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUBMIT_SHARED_SECRET", "s3cret")
    event = {
        "requestContext": {"http": {"method": "POST"}},
        "headers": {"x-submit-token": "wrong"},
        "body": "{}",
    }
    resp = submit.handler(event, None)
    assert resp["statusCode"] == 401


def test_submit_accepts_correct_secret_and_routes_to_pr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUBMIT_SHARED_SECRET", "s3cret")
    monkeypatch.setattr(submit, "_open_pull_request", lambda form: "https://github.com/x/pull/1")
    event = {
        "requestContext": {"http": {"method": "POST"}},
        "headers": {"x-submit-token": "s3cret"},
        "body": "{}",
    }
    resp = submit.handler(event, None)
    assert resp["statusCode"] == 200
    assert "pull/1" in resp["body"]
