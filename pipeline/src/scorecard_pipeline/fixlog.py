"""The fix log: a durable, dated record of findings that cleared on this feed.

The agency page already shows "fixed since the last check", but that line is
gone the next day. A manager assembling a board packet or an NTD narrative
needs the durable version: finding X was present through date A and verified
gone by the check on date B, at a URL they can cite (docs/
expansion-ideation-2026-07.md, "fix verification as a product").

Receipts are computed in the collect step while ``rebuild_index`` is already
walking every dated artifact in date order, then written per agency as
``fixlog.json`` next to the badge. New receipts merge into the existing file
rather than replacing it, so a receipt outlives the dated artifacts it was
derived from if those are ever pruned.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def finding_codes(artifact: dict[str, Any]) -> dict[str, str]:
    """Map each finding code in an artifact to its 'what' text, across measured
    categories only, mirroring the agency page's "fixed since last check" diff
    so a receipt never claims a fix in a category that simply went unmeasured."""
    return {code: what for code, (_cat, what) in _codes_with_category(artifact).items()}


def _codes_with_category(artifact: dict[str, Any]) -> dict[str, tuple[str, str]]:
    """Each measured finding code mapped to (category key, 'what' text)."""
    out: dict[str, tuple[str, str]] = {}
    for key, cat in artifact.get("categories", {}).items():
        if cat.get("status") == "measured":
            for f in cat.get("findings", []):
                code = f.get("code")
                if code:
                    out.setdefault(str(code), (str(key), str(f.get("what", ""))))
    return out


def _measured_keys(artifact: dict[str, Any]) -> set[str]:
    return {
        key
        for key, cat in artifact.get("categories", {}).items()
        if cat.get("status") == "measured"
    }


def diff_receipts(
    prev: dict[str, Any] | None,
    cur: dict[str, Any],
) -> list[dict[str, str]]:
    """Receipts for findings present in ``prev`` and verified gone in ``cur``.

    Verified is the operative word: a receipt is minted only when the finding's
    category was actually measured in the current run. A category that went
    unmeasured (a failed fetch, a realtime outage) makes its findings invisible,
    and an invisible finding is not a fixed one — this is a permanent, citable
    record, so it must never claim a fix that did not happen.

    Each receipt records the last date the finding was seen, the date of the
    check that verified it gone, the code, and the previous run's plain-language
    description (the wording the receipt's reader saw while it was open).
    """
    if not prev:
        return []
    current = finding_codes(cur)
    measured_now = _measured_keys(cur)
    last_seen = str(prev.get("snapshot_date", ""))
    verified = str(cur.get("snapshot_date", ""))
    return [
        {"code": code, "what": what, "last_seen": last_seen, "cleared": verified}
        for code, (cat_key, what) in _codes_with_category(prev).items()
        if code not in current and cat_key in measured_now
    ]


def merge_receipts(
    existing: list[dict[str, str]],
    new: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Union of receipts, keyed by (cleared date, code), oldest first.

    A finding can clear, come back, and clear again; those are distinct
    receipts. Re-running collect over the same dated files must not duplicate
    anything, and receipts already in the file survive even when the dated
    artifacts they came from are gone.
    """
    seen: dict[tuple[str, str], dict[str, str]] = {
        (r.get("cleared", ""), r.get("code", "")): r for r in existing
    }
    for r in new:
        seen.setdefault((r.get("cleared", ""), r.get("code", "")), r)
    return sorted(seen.values(), key=lambda r: (r.get("cleared", ""), r.get("code", "")))


def load_fixlog(agency_dir: Path) -> list[dict[str, str]]:
    """The receipts already recorded for this agency, oldest first; empty when
    the file is missing or unreadable (an unreadable log is rebuilt, not fatal)."""
    try:
        data = json.loads((agency_dir / "fixlog.json").read_text())
    except (FileNotFoundError, ValueError, OSError):
        return []
    receipts = data.get("receipts", []) if isinstance(data, dict) else []
    return [r for r in receipts if isinstance(r, dict)]
