import geopandas as gpd

gdb_path = "data/kenya_counties/ken_admin_boundaries.gdb"
layer_name = "ken_admbnda_adm1_iebc_20191031"   # <-- update if different

gdf = gpd.read_file(gdb_path, layer=layer_name)
print(f"Rows: {len(gdf)}")
print(f"Columns: {list(gdf.columns)}")
print("\nFirst row (no geometry):")
print(gdf.iloc[0].drop('geometry').to_dict())