"""Tract-level equity: the served-area refinement of the state overlay.

The state overlay (equity.py, ADR 0015) is a triage cut: a low-need state can
hide a high-need city. The refinement is to locate each feed's stops in their
Census tracts and aggregate ACS indicators over the tracts a feed actually
serves, so the need score reflects the riders near the stops, not the state
average.

This module is the geospatial core: a correct point-in-polygon test (ray casting,
holes handled), a bbox-prefiltered locate, and a stop-weighted aggregation of
tract indicators into one served-area need profile. It reuses the same
``EquityIndicators`` and ``need_tier`` the state overlay uses, so the consumer
side is unchanged; only the resolution improves.

The geometry and aggregation are pure and unit-tested. Loading real tract
polygons (Census TIGER) and tract ACS values is the data step that feeds these
functions; it runs where that data is reachable, not in this module.
"""

from __future__ import annotations

from dataclasses import dataclass

from .equity import EquityIndicators, need_tier

# A geographic ring is a closed list of (lon, lat) vertices; a polygon is one or
# more rings, the first the outer boundary and any others holes (GeoJSON order).
Ring = list[tuple[float, float]]
Polygon = list[Ring]


@dataclass(frozen=True)
class Tract:
    """One Census tract: its id, geometry, and ACS indicators."""

    geoid: str
    polygon: Polygon
    indicators: EquityIndicators

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        lons = [x for ring in self.polygon for x, _ in ring]
        lats = [y for ring in self.polygon for _, y in ring]
        return (min(lons), min(lats), max(lons), max(lats))


def _point_in_ring(lon: float, lat: float, ring: Ring) -> bool:
    """Ray-casting test: is (lon, lat) inside the ring. A point on the boundary
    may read either way, which is fine for tract assignment."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        # Does a horizontal ray from the point cross this edge?
        if (yi > lat) != (yj > lat):
            x_cross = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < x_cross:
                inside = not inside
        j = i
    return inside


def point_in_polygon(lon: float, lat: float, polygon: Polygon) -> bool:
    """Inside the outer ring and outside every hole."""
    if not polygon or not _point_in_ring(lon, lat, polygon[0]):
        return False
    return not any(_point_in_ring(lon, lat, hole) for hole in polygon[1:])


def _in_bbox(lon: float, lat: float, bbox: tuple[float, float, float, float]) -> bool:
    return bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]


def locate(lon: float, lat: float, tracts: list[Tract]) -> Tract | None:
    """The tract containing a point, or None. A bounding-box prefilter skips the
    polygon test for tracts the point cannot be in, which keeps the scan cheap;
    a real spatial index is the optimization once the tract set is national."""
    for tract in tracts:
        if _in_bbox(lon, lat, tract.bbox) and point_in_polygon(lon, lat, tract.polygon):
            return tract
    return None


def _weighted_mean(pairs: list[tuple[float, int]]) -> float | None:
    """Mean of values weighted by integer counts; None when no weighted value."""
    total_w = sum(w for _, w in pairs)
    if total_w == 0:
        return None
    return sum(v * w for v, w in pairs) / total_w


def served_area_indicators(
    stop_points: list[tuple[float, float]], tracts: list[Tract]
) -> EquityIndicators:
    """Aggregate tract ACS indicators over the tracts a feed's stops fall in.

    Each served tract is weighted by how many of the feed's stops land in it, so a
    tract where most service sits counts more than one with a single stop. A stop
    that falls in no tract (off the map, or a gap in coverage) is skipped. The
    result is one served-area indicator set, ready for ``need_tier``.
    """
    counts: dict[str, int] = {}
    by_geoid: dict[str, Tract] = {}
    for lon, lat in stop_points:
        tract = locate(lon, lat, tracts)
        if tract is None:
            continue
        counts[tract.geoid] = counts.get(tract.geoid, 0) + 1
        by_geoid[tract.geoid] = tract

    def _agg(get: str) -> float | None:
        pairs = [
            (getattr(by_geoid[g].indicators, get), counts[g])
            for g in counts
            if getattr(by_geoid[g].indicators, get) is not None
        ]
        return _weighted_mean(pairs)

    return EquityIndicators(
        poverty_pct=_agg("poverty_pct"),
        zero_vehicle_pct=_agg("zero_vehicle_pct"),
        disability_pct=_agg("disability_pct"),
    )


def served_area_need(
    stop_points: list[tuple[float, float]], tracts: list[Tract]
) -> tuple[str, EquityIndicators]:
    """The need tier and indicators for a feed's served area, from its stops."""
    indicators = served_area_indicators(stop_points, tracts)
    return need_tier(indicators), indicators
