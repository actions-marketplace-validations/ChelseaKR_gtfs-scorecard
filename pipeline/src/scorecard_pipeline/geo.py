"""Per-agency geometry for the national map.

The artifacts carry scores but no location, so a national map has nothing to
plot. This derives a small, stable geometry for each feed from its stops: a
representative point (the median stop, robust to one mislocated stop or a depot
far from the service area) and a bounding box. It is intentionally tiny, a point
and a box rather than the full stop cloud, so the map stays a single small file
served from object storage with no tile server (docs/expansion.md, Phase B).

Coordinates are read from stops.txt; rows without a usable lat/lon are skipped,
and a feed with no located stops yields None rather than a point at (0, 0).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .gtfs import read_tables


@dataclass(frozen=True)
class AgencyGeo:
    lon: float
    lat: float
    bbox: tuple[float, float, float, float]  # min_lon, min_lat, max_lon, max_lat
    stop_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "lon": round(self.lon, 5),
            "lat": round(self.lat, 5),
            "bbox": [round(v, 5) for v in self.bbox],
            "stop_count": self.stop_count,
        }


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _coord(row: dict[str, str], field: str) -> float | None:
    raw = row.get(field, "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def agency_geo_from_stops(stops: list[dict[str, str]]) -> AgencyGeo | None:
    """A representative point and bounding box from stop coordinates, or None.

    The point is the per-axis median, which sits inside the service area even
    when a feed lists a maintenance yard or a typo'd stop far from the rest.
    Coordinates outside the valid lat/lon range are dropped as bad data.
    """
    lons: list[float] = []
    lats: list[float] = []
    for row in stops:
        lon = _coord(row, "stop_lon")
        lat = _coord(row, "stop_lat")
        if lon is None or lat is None:
            continue
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            continue
        if lon == 0.0 and lat == 0.0:  # null island: almost always a missing value
            continue
        lons.append(lon)
        lats.append(lat)
    if not lons:
        return None
    return AgencyGeo(
        lon=_median(lons),
        lat=_median(lats),
        bbox=(min(lons), min(lats), max(lons), max(lats)),
        stop_count=len(lons),
    )


def agency_geo_from_zip(gtfs_zip_path: str) -> dict[str, Any] | None:
    """Geometry for a feed zip, as a JSON-ready dict, or None when unlocatable."""
    stops = read_tables(gtfs_zip_path, ["stops.txt"]).get("stops.txt", [])
    geo = agency_geo_from_stops(stops)
    return geo.to_dict() if geo else None
