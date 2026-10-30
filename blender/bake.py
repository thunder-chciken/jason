"""Build the Mehnert model, bake Cycles lightmaps, and export web files.

Run headless:  blender -b --factory-startup --python bake.py -- [samples] [scale]
  samples: Cycles samples per lightmap texel (default 512)
  scale:   lightmap resolution multiplier (1.0 = 4096 for the house)
Outputs go to site/model/: mehnert.gltf + images, lm_*.jpg lightmaps, bake.json."""
import bpy, math, os, sys, json, time, runpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "ph_assets")
OUT = os.path.join(HERE, "site", "model")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAMPLES = int(args[0]) if len(args) > 0 else 512
SCALE = float(args[1]) if len(args) > 1 else 1.0
F = 0.3048
EXPOSURE = 6.0          # lightmap stores irradiance / EXPOSURE, sRGB-encoded
os.makedirs(OUT, exist_ok=True)
t0 = time.time()


def log(*a):
    print(f"[bake {time.time() - t0:6.1f}s]", *a, flush=True)


# ------------------------------------------------------------------ build
bpy.ops.wm.read_factory_settings(use_empty=True)
runpy.run_path(os.path.join(HERE, "model.py"), run_name="__main__")
runpy.run_path(os.path.join(HERE, "furnish.py"), run_name="lib_furnish")["run"]()
scene = bpy.context.scene
log("built", len(bpy.data.objects), "objects")

# ------------------------------------------------------------------ lighting
K = (21.0 - 15.1667) / 35.0
zr = lambda fy: 21.0 - (35 - fy) * K
zs = lambda fy: 18.833 - (35 - fy) * K
zb = lambda fy: 12.4 - ((35 - fy) - 17.0) * (1.3 / 15.3)

world = bpy.data.worlds.new("Sky")
scene.world = world
world.use_nodes = True
nt = world.node_tree
bg = nt.nodes["Background"]
env = nt.nodes.new("ShaderNodeTexEnvironment")
hdr_path = os.path.join(ASSETS, "kloofendal_48d_partly_cloudy_puresky", "sky_2k.hdr")
env.image = bpy.data.images.load(hdr_path)
mapping = nt.nodes.new("ShaderNodeMapping")
coord = nt.nodes.new("ShaderNodeTexCoord")
nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
nt.links.new(env.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0

# find the sun in the HDRI and rotate the sky so the sun sits south-southwest
w, h = env.image.size
px = np.array(env.image.pixels[:], dtype=np.float32).reshape(h, w, 4)
lum = px[..., 0] * 0.2126 + px[..., 1] * 0.7152 + px[..., 2] * 0.0722
iy, ix = np.unravel_index(np.argmax(lum), lum.shape)
u, v = (ix + 0.5) / w, (iy + 0.5) / h
phi_sun = (u - 0.5) * 2 * math.pi                       # Blender: u = atan2(y, -x)/2pi + 0.5
elev = (v - 0.5) * math.pi                               # pixel rows run bottom-up
theta_t = math.atan2(-1.0, -0.35)                       # desired sun direction (toward south-southwest)
alpha = math.pi - theta_t - phi_sun
mapping.inputs["Rotation"].default_value[2] = alpha
log(f"sun at u={u:.3f} v={v:.3f} elevation={math.degrees(elev):.1f} deg, sky rotated {math.degrees(alpha):.1f} deg")


def point(name, x, fy, z, watts, color=(1.0, 0.86, 0.72), radius=0.08):
    d = bpy.data.lights.new(name, "POINT")
    d.energy = watts
    d.color = color
    d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d)
    o.location = (x * F, (35 - fy) * F, z * F)
    scene.collection.objects.link(o)


for (x, fy) in ((3, 2.5), (11, 2.5), (3, 13.5), (11, 13.5), (17.5, 2.0), (18.2, 10.0), (3, 25), (10, 25),
                (3, 32), (10, 32), (18.2, 25), (12.2, 18.6), (17, 18.6), (5, 19.4), (24.5, 5.5), (24.5, 11.5)):
    point("can", x, fy, 8.7, 22)
for fy in (9.0, 11.2, 13.4):
    point("pendant", 30.05, fy, 6.75, 18)
point("living_fill", 34.5, 26.0, 12.0, 60, radius=0.6)
point("loft_fill_a", 9.0, 12.0, 15.0, 35, radius=0.5)
point("loft_fill_b", 12.0, 27.0, 17.0, 35, radius=0.5)
for (x, fy) in ((57, 10), (65, 10), (57, 22), (65, 22), (70, 30)):
    point("studio", x, fy, zs(fy) - 0.4, 45)
for (x, fy) in ((80, 12), (80, 26)):
    point("garage", x, fy, zs(fy) - 0.4, 40)
for fy in (10.0, 15.0):
    point("breezeway", 46, fy, zb(fy) - 0.4, 22)
for x in (6.5, 33.5):
    point("porch", x, 39.0, 9.2, 15)

# ------------------------------------------------------------------ cycles
prefs = bpy.context.preferences.addons["cycles"].preferences
for kind in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = kind
        prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            break
    except Exception:
        pass
for d in prefs.devices:
    d.use = d.type in ("OPTIX", "CUDA")
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.samples = SAMPLES
scene.cycles.max_bounces = 8
scene.cycles.diffuse_bounces = 5
scene.cycles.glossy_bounces = 2
scene.cycles.transparent_max_bounces = 8
scene.cycles.use_denoising = False
scene.render.bake.margin = 6
scene.render.bake.use_clear = True
log("device", prefs.compute_device_type, [d.name for d in prefs.devices if d.use])

GROUPS = {"LM_house": 4096, "LM_studio": 4096, "LM_furn": 2048, "LM_site": 2048}
bake_info = {"exposure": EXPOSURE, "sky_rotation_deg": math.degrees(alpha), "sun_elevation_deg": math.degrees(elev),
             "groups": {}}


def unwrap(ob):
    lm = ob.data.uv_layers.new(name="LM")
    ob.data.uv_layers["UVMap"].active_render = True
    ob.data.uv_layers.active = lm
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")


def blur_islands(rgb, mask, passes=2):
    """Gentle 3x3 blur that never pulls color from outside the UV islands."""
    m = mask.astype(np.float32)
    for _ in range(passes):
        acc = np.zeros_like(rgb)
        wsum = np.zeros(mask.shape, np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                wgt = 1.0 if dx == 0 and dy == 0 else 0.6
                acc += np.roll(np.roll(rgb * m[..., None], dy, 0), dx, 1) * wgt
                wsum += np.roll(np.roll(m, dy, 0), dx, 1) * wgt
        out = acc / np.maximum(wsum, 1e-6)[..., None]
        rgb = np.where(mask[..., None], out, rgb)
    return rgb


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


for gname, size in GROUPS.items():
    ob = bpy.data.objects.get(gname)
    if not ob:
        continue
    size = int(size * SCALE)
    for slot in ob.material_slots:
        if slot.material:
            m = slot.material.copy()
            m.name = slot.material.name.split("@")[0] + "@" + gname
            slot.material = m
    unwrap(ob)
    img = bpy.data.images.new("lm_" + gname, size, size, float_buffer=True, alpha=True)
    for slot in ob.material_slots:
        m = slot.material
        if not m:
            continue
        m.use_nodes = True
        node = m.node_tree.nodes.new("ShaderNodeTexImage")
        node.name = "LM_BAKE"
        node.image = img
        m.node_tree.nodes.active = node
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    log("baking", gname, size, "px", SAMPLES, "samples")
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=6, use_clear=True,
                        target="IMAGE_TEXTURES")
    px = np.array(img.pixels[:], dtype=np.float32).reshape(size, size, 4)
    rgb, mask = px[..., :3], px[..., 3] > 0.5
    rgb = blur_islands(rgb, mask)
    enc = srgb(rgb / EXPOSURE)
    out = bpy.data.images.new("lm_" + gname + "_8bit", size, size, alpha=False)
    out.pixels[:] = np.concatenate([enc, np.ones((size, size, 1), np.float32)], -1).ravel()
    path = os.path.join(OUT, f"lm_{gname}.jpg")
    out.filepath_raw = path
    out.file_format = "JPEG"
    scene.render.image_settings.quality = 88
    out.save(filepath=path, quality=88)
    bake_info["groups"][gname] = {"file": f"lm_{gname}.jpg", "size": size,
                                  "mean": float(rgb[mask].mean()) if mask.any() else 0.0}
    for slot in ob.material_slots:
        n = slot.material.node_tree.nodes.get("LM_BAKE") if slot.material else None
        if n:
            slot.material.node_tree.nodes.remove(n)
    log("done", gname, "mean irradiance", round(bake_info["groups"][gname]["mean"], 3))

# ------------------------------------------------------------------ export
for o in list(scene.objects):
    if o.type == "LIGHT":
        bpy.data.objects.remove(o, do_unlink=True)
col = bpy.data.collections["Mehnert"]
for o in bpy.context.view_layer.objects:
    o.select_set(o.name in col.objects)
gltf = os.path.join(OUT, "mehnert.gltf")
bpy.ops.export_scene.gltf(filepath=gltf, export_format="GLTF_SEPARATE", use_selection=True, export_apply=True,
                          export_image_format="AUTO", export_jpeg_quality=85, export_cameras=False,
                          export_lights=False, export_yup=True, export_texcoords=True, export_normals=True,
                          export_meshopt_compression_enable=True, export_meshopt_extension="EXT_meshopt_compression")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "mehnert_baked.blend"))
with open(os.path.join(OUT, "bake.json"), "w") as f:
    json.dump(bake_info, f, indent=2)
log("exported", gltf)
