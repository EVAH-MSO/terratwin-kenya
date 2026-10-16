import osmium
import json
from app.db import get_connection

PBF_PATH = "data/kenya-261014.osm.pbf"

ROAD_TYPES = {
    "motorway", "motorway_link",
    "trunk", "trunk_link",
    "primary", "primary_link",
    "secondary", "secondary_link",
    "tertiary", "tertiary_link",
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

        coords = [(n.lon, n.lat) for n in w.nodes]
        if len(coords) < 2:
            return

        self.roads.append({
            "name": w.tags.get("name", "")[:255],
            "highway": hw,
            "coords": coords,
        })


print(f"Reading {PBF_PATH}...")
print("(This takes 5-15 minutes)")

handler = RoadHandler()
handler.apply_file(PBF_PATH, locations=True)

print(f"Found {len(handler.roads)} major road segments")

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
    geom = {"type": "LineString", "coordinates": road["coords"]}
    cursor.execute(
        "INSERT INTO roads (name, highway, geometry) VALUES (%s, %s, %s)",
        (road["name"] or None, road["highway"], json.dumps(geom))
    )
    count += 1
    if count % 2000 == 0:
        print(f"  Inserted {count}...")

conn.close()
print(f"✅ Loaded {count} road segments into Azure SQL")
