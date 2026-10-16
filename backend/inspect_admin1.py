import geopandas as gpd

GDB_PATH = "data/kenya_counties/ken_admin_boundaries.gdb"

gdf = gpd.read_file(GDB_PATH, layer="ken_admin1")
print(f"Rows: {len(gdf)}")
print(f"Columns: {list(gdf.columns)}")
print(f"\nFirst row properties:")
print(gdf.iloc[0].drop("geometry").to_dict())
print(f"\nGeometry type: {gdf.geometry.geom_type.iloc[0]}")
