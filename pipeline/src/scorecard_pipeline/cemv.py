"""Detect declared contactless-payment support (cEMV) in a feed.

The GTFS community adopted the ``cemv_support`` field on 2025-09-29
(google/transit#545): agency.txt and routes.txt rows can declare whether a
rider can pay with a contactless bank card on that agency or route. Adoption
is brand new, which is exactly why the What-feeds-publish page tracks it:
this watches an optional field spread from day one, framed as adoption and
never as quality (a feed without it is early, not failing).

Values per the spec: 1 = riders can use cEMV, 2 = riders cannot. A feed
"declares" cEMV when either file carries the column at all; it "supports"
cEMV when any row declares 1.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from typing import Any

from .gtfs import _read_table


@dataclass(frozen=True)
class CemvProfile:
    """What the feed says about contactless bank-card payment."""

    declared: bool  # the cemv_support column exists in agency.txt or routes.txt
    supported: bool  # any row declares cemv_support = 1

    def to_details(self) -> dict[str, Any]:
        return {"declared": self.declared, "supported": self.supported}


def detect_cemv(gtfs_zip_path: str) -> CemvProfile:
    """Read cemv_support from agency.txt and routes.txt, tolerating absence.

    A missing column is the overwhelmingly common case today and reads as
    "not declared", never as an error; a malformed zip yields the same so a
    brand-new optional field can never fail a score.
    """
    declared = False
    try:
        with zipfile.ZipFile(gtfs_zip_path) as zf:
            for name in ("agency.txt", "routes.txt"):
                for row in _read_table(zf, name):
                    if "cemv_support" in row:
                        declared = True
                        if str(row.get("cemv_support", "")).strip() == "1":
                            return CemvProfile(declared=True, supported=True)
    except (zipfile.BadZipFile, OSError, ValueError):
        return CemvProfile(declared=False, supported=False)
    return CemvProfile(declared=declared, supported=False)
