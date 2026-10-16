import osmium
import json
from app.db import get_connection

PBF_PATH = "data/kenya-261014.osm.pbf"

# ALL road types — including residential, service
ROAD_TYPES = {
    "motorway", "motorway_link",
    "trunk", "trunk_link",
    "primary", "primary_link",
    "secondary", "secondary_link",
    "tertiary", "tertiary_link",
    "residential", "unclassified", "living_street",
    "service", "road", "track",
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
        try:
            coords = [(n.lon, n.lat) for n in w.nodes]
            if len(coords) < 2:
                return
            name = w.tags.get("name", "")
            self.roads.append({
                "name": name[:200] if name else "",
                "highway": hw,
                "coords": coords,
            })
        except Exception:
            return


print(f"Reading {PBF_PATH}...")
print("(This takes 10-20 minutes for the full Kenya extract)")
handler = RoadHandler()
handler.apply_file(PBF_PATH, locations=True)
print(f"Found {len(handler.roads)} road segments")

conn = get_connection()
cursor = conn.cursor()
cursor.execute("DELETE FROM roads")
print("Cleared old roads...")

count = 0
BATCH = 500
batch_data = []
for road in handler.roads:
    geom = {"type": "LineString", "coordinates": road["coords"]}
    batch_data.append((road["name"] or None, road["highway"], json.dumps(geom)))
    if len(batch_data) >= BATCH:
        cursor.executemany(
            "INSERT INTO roads (name, highway, geometry) VALUES (%s, %s, %s)",
            batch_data
        )
        count += len(batch_data)
        batch_data = []
        if count % 5000 == 0:
            print(f"  Inserted {count}...")

if batch_data:
    cursor.executemany(
        "INSERT INTO roads (name, highway, geometry) VALUES (%s, %s, %s)",
        batch_data
    )
    count += len(batch_data)

conn.close()
print(f"✅ Loaded {count} road segments")
