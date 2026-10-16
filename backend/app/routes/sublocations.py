import json
from fastapi import APIRouter, Query
from app.db import get_connection

router = APIRouter(prefix="/sublocations", tags=["sublocations"])

@router.get("")
def list_sublocations(
    county: str = Query(None),
    limit: int = Query(500),
):
    conn = get_connection()
    cursor = conn.cursor()
    sql = f"SELECT TOP {limit} name, county, pcode, geometry FROM sublocations WHERE 1=1"
    params = []
    if county:
        sql += " AND county LIKE %s"
        params.append(f"%{county}%")
    sql += " ORDER BY name"
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    features = []
    for name, cty, pcode, geom_json in rows:
        features.append({
            "type": "Feature",
            "properties": {"name": name, "county": cty, "pcode": pcode},
            "geometry": json.loads(geom_json),
        })
    return {"type": "FeatureCollection", "features": features}
