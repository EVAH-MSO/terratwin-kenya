import osmium
import json
from app.db import get_connection

PBF_PATH = "data/kenya-latest.osm.pbf"

# Filter: collect all ways that are roads
ROAD_TYPES = {
    "motorway", "motorway_link",
    "trunk", "trunk_link",
    "primary", "primary_link",
    "secondary", "secondary_link",
    "tertiary", "tertiary_link",
    "residential", "unclassified",
    "service", "living_street",
}

class RoadHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.roads = []

    def way(self, w):
        if "highway" not in w.tags:
            return
        hw = w.tags["highway"]
        if hw not in ROAD_TYPES:
            return

        # Only keep ways with at least 2 nodes
        coords = [(n.lon, n.lat) for n in w.nodes]
        if len(coords) < 2:
            return

        self.roads.append({
            "name": w.tags.get("name", ""),
            "highway": hw,
            "coords": coords
        })

print(f"Reading {PBF_PATH}...")
print("(This takes 3-8 minutes for the full Kenya extract)")

handler = RoadHandler()
handler.apply_file(PBF_PATH, locations=True)

print(f"Found {len(handler.roads)} road segments")

# Save to DB
conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='roads' AND xtype='U')
    CREATE TABLE roads (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(255),
        highway NVARCHAR(50),
        geometry NVARCHAR(MAX)
    )
""")
cursor.execute("DELETE FROM roads")

count = 0
for road in handler.roads:
    # GeoJSON LineString format
    geom = {
        "type": "LineString",
        "coordinates": road["coords"]
    }
    geom_json = json.dumps(geom)

    cursor.execute(
        "INSERT INTO roads (name, highway, geometry) VALUES (%s, %s, %s)",
        (road["name"][:255] if road["name"] else None, road["highway"], geom_json)
    )
    count += 1

    if count % 10000 == 0:
        print(f"  Inserted {count}...")

conn.close()
print(f"✅ Loaded {count} road segments")
