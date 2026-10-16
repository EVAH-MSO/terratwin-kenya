import pyogrio

gdb_path = "data/kenya_counties/ken_admin_boundaries.gdb"

print("Layers found:")
layers = pyogrio.list_layers(gdb_path)
for layer_name, geom_type in layers:
    print(f"  - {layer_name} ({geom_type})")
