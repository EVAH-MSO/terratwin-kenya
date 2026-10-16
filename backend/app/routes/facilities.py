from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.db import get_connection
from app.models.schemas import Facility

router = APIRouter(prefix="/facilities", tags=["facilities"])


def _row_to_facility(row):
    return Facility(
        id=row[0], name=row[1], type=row[2], county=row[3] or "Unknown",
        latitude=row[4], longitude=row[5]
    )


@router.get("", response_model=List[Facility])
def list_facilities(
    type: Optional[str] = Query(None),
    county: Optional[str] = Query(None),
    limit: int = Query(2000),
):
    conn = get_connection()
    cursor = conn.cursor()
    sql = f"SELECT TOP {limit} id, name, type, county, latitude, longitude FROM facilities WHERE 1=1"
    params = []
    if type:
        sql += " AND type = %s"
        params.append(type)
    if county:
        sql += " AND county LIKE %s"
        params.append(f"%{county}%")
    sql += " ORDER BY name"
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_facility(r) for r in rows]


@router.get("/nearest")
def nearest_facility(lat: float = Query(...), lon: float = Query(...), type: str = Query("hospital")):
    import math
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, type, county, latitude, longitude FROM facilities WHERE type = %s",
        (type,)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"error": "No facilities of that type"}

    def hav(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return 2 * R * math.asin(math.sqrt(a))

    best = min(rows, key=lambda r: hav(lat, lon, r[4], r[5]))
    d = hav(lat, lon, best[4], best[5])
    return {
        "id": best[0], "name": best[1], "type": best[2], "county": best[3] or "Unknown",
        "latitude": best[4], "longitude": best[5],
        "distance_km": round(d, 2),
        "from": {"lat": lat, "lon": lon}
    }


@router.get("/{facility_id}", response_model=Facility)
def get_facility(facility_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, type, county, latitude, longitude FROM facilities WHERE id = %s",
        (facility_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Facility not found")
    return _row_to_facility(row)
