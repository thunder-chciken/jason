"""Turn the Blender glTF export into files the artifact host serves:
the .bin buffer is inlined as base64 so the model is one .json plus .jpg/.png images."""
import base64, json, os, shutil
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(HERE, "site", "model")
g = json.load(open(os.path.join(M, "mehnert.gltf"), encoding="utf-8"))
for b in g["buffers"]:
    if "uri" not in b:          # EXT_meshopt_compression fallback buffer has no data
        continue
    raw = open(os.path.join(M, b["uri"]), "rb").read()
    b["uri"] = "data:application/octet-stream;base64," + base64.b64encode(raw).decode()
with open(os.path.join(M, "mehnert.json"), "w", encoding="utf-8") as f:
    json.dump(g, f, separators=(",", ":"))

sky = os.path.join(os.path.dirname(HERE), "ph_assets", "kloofendal_48d_partly_cloudy_puresky", "sky_tonemapped.jpg")
im = Image.open(sky).convert("RGB")
im.resize((2048, 1024), Image.LANCZOS).save(os.path.join(M, "sky.jpg"), quality=86)

used = {i["uri"] for i in g.get("images", []) if "uri" in i}
files = sorted(used | {"mehnert.json", "sky.jpg", "bake.json"} | {f for f in os.listdir(M) if f.startswith("lm_")})
total = sum(os.path.getsize(os.path.join(M, f)) for f in files)
json.dump(files, open(os.path.join(HERE, "site", "files.json"), "w"), indent=0)
print(len(files), "files", round(total / 1e6, 1), "MB; largest:",
      sorted(((os.path.getsize(os.path.join(M, f)), f) for f in files), reverse=True)[:4])
print("extensions:", g.get("extensionsUsed"), "required:", g.get("extensionsRequired"))
