import pyogrio

gdb_path = "data/kenya_counties/ken_admin_boundaries.gdb"

# List all layers inside the GDB
layers = pyogrio.list_layers(gdb_path)
print("Layers found:")
for layer_name, geom_type in layers:
    print(f"  - {layer_name} ({geom_type})") 