import osmium
import json
from app.db import get_connection

PBF_PATH = "data/kenya-261014.osm.pbf"

# OSM tags for facilities we want
FACILITY_TAGS = {
    "amenity": {
        "hospital": "hospital",
        "clinic": "hospital",
        "doctors": "hospital",
        "school": "school",
        "college": "school",
        "university": "school",
        "police": "police",
        "fire_station": "fire",
    }
}


class FacilityHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.facilities = []

    def node(self, n):
        if not n.tags:
            return
        amenity = n.tags.get("amenity")
        if amenity not in FACILITY_TAGS["amenity"]:
            return
        name = n.tags.get("name") or n.tags.get("name:en")
        if not name:
            return
        self.facilities.append({
            "name": name[:200],
            "type": FACILITY_TAGS["amenity"][amenity],
            "lat": n.location.lat,
            "lon": n.location.lon,
        })

    def way(self, w):
        if not w.tags:
            return
        amenity = w.tags.get("amenity")
        if amenity not in FACILITY_TAGS["amenity"]:
            return
        name = w.tags.get("name") or w.tags.get("name:en")
        if not name:
            return
        try:
            # Centroid of way
            coords = [(n.lon, n.lat) for n in w.nodes]
            if not coords:
                return
            avg_lon = sum(c[0] for c in coords) / len(coords)
            avg_lat = sum(c[1] for c in coords) / len(coords)
            self.facilities.append({
                "name": name[:200],
                "type": FACILITY_TAGS["amenity"][amenity],
                "lat": avg_lat,
                "lon": avg_lon,
            })
        except Exception:
            return


print(f"Reading {PBF_PATH}...")
print("(This takes 2-5 minutes)")

handler = FacilityHandler()
handler.apply_file(PBF_PATH, locations=True)

print(f"Found {len(handler.facilities)} facilities")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='facilities' AND xtype='U')
    CREATE TABLE facilities (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(200) NOT NULL,
        type NVARCHAR(50) NOT NULL,
        county NVARCHAR(100),
        latitude FLOAT,
        longitude FLOAT
    )
""")
cursor.execute("DELETE FROM facilities")

count = 0
for f in handler.facilities:
    cursor.execute(
        "INSERT INTO facilities (name, type, latitude, longitude) VALUES (%s, %s, %s, %s)",
        (f["name"], f["type"], f["lat"], f["lon"])
    )
    count += 1
    if count % 500 == 0:
        print(f"  Inserted {count}...")

conn.close()
print(f"✅ Loaded {count} facilities into Azure SQL")
