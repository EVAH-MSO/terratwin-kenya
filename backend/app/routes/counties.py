from fastapi import APIRouter, HTTPException
from typing import List
from app.db import get_connection
from app.models.schemas import County

router = APIRouter(prefix="/counties", tags=["counties"])


def _row_to_county(row):
    return County(
        id=row[0], code=row[1], name=row[2], capital=row[3],
        population=row[4], area_km2=row[5]
    )


@router.get("", response_model=List[County])
def list_counties():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, code, name, capital, population, area_km2 FROM counties ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_county(r) for r in rows]


@router.get("/search/{name}", response_model=List[County])
def search_counties(name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, code, name, capital, population, area_km2 FROM counties WHERE name LIKE %s ORDER BY name",
        (f"%{name}%",)
    )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_county(r) for r in rows]


@router.get("/{county_id}/stats")
def county_stats(county_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM counties WHERE id = %s", (county_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="County not found")
    county_name = row[0]

    try:
        cursor.execute("SELECT COUNT(*) FROM sublocations WHERE county = %s", (county_name,))
        sub_count = cursor.fetchone()[0]
    except Exception:
        sub_count = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM facilities WHERE county = %s", (county_name,))
        fac_count = cursor.fetchone()[0]
    except Exception:
        fac_count = 0

    conn.close()
    return {
        "county": county_name,
        "sublocations": sub_count,
        "facilities": fac_count,
    }


@router.get("/{county_id}", response_model=County)
def get_county(county_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, code, name, capital, population, area_km2 FROM counties WHERE id = %s",
        (county_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="County not found")
    return _row_to_county(row)
