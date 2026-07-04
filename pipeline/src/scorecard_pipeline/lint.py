"""Registry hygiene checks.

The Mobility Database sync can pull in entries whose `name` is the catalog's
feed descriptor ("Flex", "Bus", "Do not use - deprecated") rather than the
transit provider. These checks catch that, plus a non-HTTPS feed URL or a
missing mdb_id, so the registry stays clean as it grows. Reported by
`scorecard lint`; the descriptor set is also used by the sync so future
proposals use the provider name instead.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .config import Agency

# Catalog "name" values that describe a feed, not an agency. An agency whose name
# is one of these was synced from the wrong column; its provider name is correct.
FEED_DESCRIPTOR_NAMES = frozenset(
    {
        "do not use - deprecated",
        "flex",
        "flex v2 included",
        "flex v2",
        "static feed for realtime",
        "bus",
        "rail",
        "fixed route",
    }
)


def is_feed_descriptor(name: str) -> bool:
    """True when a name is a feed descriptor, not a real agency name."""
    return name.strip().lower() in FEED_DESCRIPTOR_NAMES


@dataclass(frozen=True)
class RegistryIssue:
    agency_id: str
    kind: str  # feed_descriptor_name | non_https_url | missing_mdb_id
    detail: str


def lint_registry(agencies: Iterable[Agency]) -> list[RegistryIssue]:
    """Hygiene issues across the registry, worst (a wrong name) first."""
    issues: list[RegistryIssue] = []
    for agency in agencies:
        if is_feed_descriptor(agency.name):
            issues.append(
                RegistryIssue(
                    agency.id,
                    "feed_descriptor_name",
                    f"name {agency.name!r} is a feed descriptor, not an agency name",
                )
            )
        if not agency.static_gtfs_url.startswith("https://"):
            issues.append(RegistryIssue(agency.id, "non_https_url", agency.static_gtfs_url))
        if not agency.mdb_id:
            issues.append(RegistryIssue(agency.id, "missing_mdb_id", ""))
    order = {"feed_descriptor_name": 0, "non_https_url": 1, "missing_mdb_id": 2}
    issues.sort(key=lambda i: (order.get(i.kind, 9), i.agency_id))
    return issues
