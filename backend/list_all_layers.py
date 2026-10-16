import pyogrio

gdb_path = "data/kenya_counties/ken_admin_boundaries.gdb"
layers = pyogrio.list_layers(gdb_path)
print(f"Total layers: {len(layers)}\n")
for name, geom in layers:
    print(f"  {name}  →  {geom}")
