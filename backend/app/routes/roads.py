import json
from fastapi import APIRouter, Query
from app.db import get_connection

router = APIRouter(prefix="/roads", tags=["roads"])


@router.get("")
def get_roads(
    min_lat: float = Query(None),
    max_lat: float = Query(None),
    min_lon: float = Query(None),
    max_lon: float = Query(None),
    limit: int = Query(3000),
):
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch roads with a hard limit (Azure SQL TOP)
    cursor.execute(f"""
        SELECT TOP {limit} name, highway, geometry
        FROM roads
        WHERE geometry IS NOT NULL
    """)
    rows = cursor.fetchall()
    conn.close()

    features = []
    for name, highway, geom_json in rows:
        try:
            geom = json.loads(geom_json)
        except Exception:
            continue

        # Bounding box filter in Python (approximate)
        if min_lat is not None and min_lon is not None and max_lat is not None and max_lon is not None:
            coords = geom.get("coordinates", [])
            if coords:
                # First point of the line
                first = coords[0]
                lon, lat = first[0], first[1]
                if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
                    continue

        features.append({
            "type": "Feature",
            "properties": {
                "name": name or "",
                "highway": highway or "road",
            },
            "geometry": geom,
        })

    return {"type": "FeatureCollection", "features": features}
