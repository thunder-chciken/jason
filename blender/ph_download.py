"""Download selected CC0 assets from Poly Haven (api.polyhaven.com) into ph_assets/<id>/."""
import json, os, sys, urllib.request

OUT = sys.argv[1]
UA = {"User-Agent": "StoryRemodelingWalkthrough/1.0"}

TEXTURES = ["laminate_floor_02", "smooth_concrete_floor", "brushed_concrete", "white_plaster_02",
            "box_profile_metal_sheet", "large_grey_tiles", "marble_mosaic_tiles", "marble_01",
            "fine_grained_wood", "hinoki_planks", "leafy_grass", "gravel_road", "dark_wood"]
MODELS = ["sofa_02", "modern_coffee_table_01", "mid_century_lounge_chair", "bar_chair_round_01",
          "potted_plant_02", "potted_plant_04", "pachira_aquatica_01", "throw_pillows_01", "ceiling_fan",
          "hanging_industrial_lamp", "modern_arm_chair_01", "decorative_book_set_01", "ceramic_vase_01",
          "ceramic_vase_02", "ceramic_vase_03", "wooden_stool_02", "covered_car", "metal_tool_chest",
          "shrub_02", "side_table_01"]
HDRIS = ["kloofendal_48d_partly_cloudy_puresky"]


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def save(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = get(url)
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


total = 0
for tid in TEXTURES:
    files = json.loads(get(f"https://api.polyhaven.com/files/{tid}"))
    for key, name in (("Diffuse", "diff"), ("nor_gl", "nor"), ("Rough", "rough")):
        if key in files and "1k" in files[key]:
            total += save(files[key]["1k"]["jpg"]["url"], os.path.join(OUT, tid, f"{name}.jpg"))
    print("tex", tid, flush=True)

for mid in MODELS:
    files = json.loads(get(f"https://api.polyhaven.com/files/{mid}"))
    if "gltf" not in files or "1k" not in files["gltf"]:
        print("skip (no glTF)", mid, flush=True)
        continue
    g = files["gltf"]["1k"]["gltf"]
    total += save(g["url"], os.path.join(OUT, mid, os.path.basename(g["url"])))
    for rel, inc in g.get("include", {}).items():
        total += save(inc["url"], os.path.join(OUT, mid, rel))
    print("model", mid, flush=True)

for hid in HDRIS:
    files = json.loads(get(f"https://api.polyhaven.com/files/{hid}"))
    total += save(files["hdri"]["2k"]["hdr"]["url"], os.path.join(OUT, hid, "sky_2k.hdr"))
    if "tonemapped" in files:
        total += save(files["tonemapped"]["url"], os.path.join(OUT, hid, "sky_tonemapped.jpg"))
    print("hdri", hid, flush=True)

print(f"downloaded {total / 1e6:.1f} MB")
