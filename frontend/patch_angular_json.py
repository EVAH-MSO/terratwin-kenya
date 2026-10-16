import json

path = "angular.json"
with open(path) as f:
    cfg = json.load(f)

# Find the build options
projects = cfg["projects"]
proj_name = list(projects.keys())[0]
opts = projects[proj_name]["architect"]["build"]["options"]

# Ensure assets has the cesium entry
assets = opts.get("assets", [])
has_cesium = any(
    isinstance(a, dict) and a.get("output") == "assets/cesium"
    for a in assets
)
if not has_cesium:
    assets.append({
        "glob": "**/*",
        "input": "node_modules/cesium/Build/Cesium",
        "output": "assets/cesium"
    })
    opts["assets"] = assets

# Ensure cesium widgets css is in styles
styles = opts.get("styles", [])
css = "node_modules/cesium/Build/Cesium/Widgets/widgets.css"
if css not in styles:
    styles.append(css)
    opts["styles"] = styles

with open(path, "w") as f:
    json.dump(cfg, f, indent=2)

print("✅ angular.json patched")
print("   assets:", assets)
print("   styles:", styles)
