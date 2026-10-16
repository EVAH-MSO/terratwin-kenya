import pyogrio
import geopandas as gpd

gdb_path = "data/kenya_counties/ken_admin_boundaries.gdb"

layers = pyogrio.list_layers(gdb_path)
print("Layers:")
for name, geom in layers:
    print(f"  - {name} ({geom})")

# Auto-pick the adm1 layer
adm1 = None
for name, geom in layers:
    if "adm1" in name.lower():
        adm1 = name
        break

if not adm1:
    print("❌ No adm1 layer found")
    exit(1)

print(f"\nReading layer: {adm1}")
gdf = gpd.read_file(gdb_path, layer=adm1)
print(f"Rows: {len(gdf)}")
print(f"Columns: {list(gdf.columns)}")
print(f"\nFirst row:")
print(gdf.iloc[0].drop("geometry").to_dict())
