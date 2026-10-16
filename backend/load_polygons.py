import geopandas as gpd
import json
from shapely.geometry import mapping
from app.db import get_connection

GDB_PATH = "data/kenya_counties/ken_admin_boundaries.gdb"
LAYER = "ken_admin1"
NAME_FIELD = "adm1_name"

print(f"Reading {LAYER}...")
gdf = gpd.read_file(GDB_PATH, layer=LAYER)
print(f"Loaded {len(gdf)} features")

conn = get_connection()
cursor = conn.cursor()

updated = 0
not_matched = []

for _, row in gdf.iterrows():
    raw_name = row[NAME_FIELD]
    if not raw_name:
        continue

    clean_name = str(raw_name).replace(" County", "").strip()

    geom = mapping(row["geometry"])
    geom_json = json.dumps(geom)

    cursor.execute(
        "UPDATE counties SET geometry = %s WHERE name = %s",
        (geom_json, clean_name)
    )
    if cursor.rowcount > 0:
        updated += 1
    else:
        not_matched.append(clean_name)

conn.close()
print(f"\n✅ Updated {updated} counties with polygon geometry")
if not_matched:
    print(f"⚠️  Did not match ({len(not_matched)}): {not_matched}")
