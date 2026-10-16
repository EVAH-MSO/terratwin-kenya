import geopandas as gpd
import json
from shapely.geometry import mapping
from app.db import get_connection

GDB_PATH = "data/kenya_counties/ken_admin_boundaries.gdb"

gdf = gpd.read_file(GDB_PATH, layer="ken_admin2")
print(f"Loaded {len(gdf)} sub-counties")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='sublocations' AND xtype='U')
    CREATE TABLE sublocations (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(200),
        county NVARCHAR(200),
        pcode NVARCHAR(50),
        geometry NVARCHAR(MAX)
    )
""")
cursor.execute("DELETE FROM sublocations")

count = 0
for _, row in gdf.iterrows():
    name = row.get("adm2_name")
    county = row.get("adm1_name")
    pcode = row.get("adm2_pcode")
    if not name:
        continue

    geom_json = json.dumps(mapping(row["geometry"]))
    cursor.execute(
        "INSERT INTO sublocations (name, county, pcode, geometry) VALUES (%s, %s, %s, %s)",
        (name, county, pcode, geom_json)
    )
    count += 1

conn.close()
print(f"✅ Loaded {count} sublocations")
