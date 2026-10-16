import json
from functools import lru_cache
from fastapi import APIRouter, Query
from app.db import get_connection

router = APIRouter(prefix="/boundaries", tags=["boundaries"])


def _simplify_ring(points, tolerance):
    if len(points) < 3:
        return points

    def sq_dist(p, p1, p2):
        x, y = p[0], p[1]
        x1, y1 = p1[0], p1[1]
        x2, y2 = p2[0], p2[1]
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return (x - x1) ** 2 + (y - y1) ** 2
        t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        px, py = x1 + t * dx, y1 + t * dy
        return (x - px) ** 2 + (y - py) ** 2

    dmax, idx = 0, 0
    for i in range(1, len(points) - 1):
        d = sq_dist(points[i], points[0], points[-1])
        if d > dmax:
            idx = i
            dmax = d

    if dmax > tolerance ** 2:
        left = _simplify_ring(points[:idx + 1], tolerance)
        right = _simplify_ring(points[idx:], tolerance)
        return left[:-1] + right
    return [points[0], points[-1]]


def _simplify_ring_safe(ring, tolerance):
    if len(ring) < 4:
        return ring
    s = _simplify_ring(ring, tolerance)
    if s[0] != s[-1]:
        s.append(s[0])
    return s


def _simplify_geometry(geom, tolerance):
    t = geom.get("type")
    if t == "Polygon":
        geom["coordinates"] = [_simplify_ring_safe(r, tolerance) for r in geom["coordinates"]]
    elif t == "MultiPolygon":
        geom["coordinates"] = [
            [_simplify_ring_safe(r, tolerance) for r in poly]
            for poly in geom["coordinates"]
        ]
    return geom


@lru_cache(maxsize=4)
def _load_and_simplify(tolerance: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, code, geometry FROM counties WHERE geometry IS NOT NULL ORDER BY name"
    )
    rows = cursor.fetchall()
    conn.close()

    features = []
    for name, code, geom_json in rows:
        geom = json.loads(geom_json)
        geom = _simplify_geometry(geom, tolerance)
        features.append({
            "type": "Feature",
            "properties": {"name": name, "code": code},
            "geometry": geom,
        })

    return {"type": "FeatureCollection", "features": features}


@router.get("/counties")
def get_county_boundaries(tolerance: float = Query(0.01)):
    return _load_and_simplify(tolerance)
