"""Place Poly Haven furniture (CC0) into the Mehnert model and join it into LM_furn.

Placements are plan feet: x east, fy measured down from the rear wall, z above the
main floor, rotation in degrees about Z (models face -Y before rotation)."""
import bpy, glob, math, os
from mathutils import Matrix, Vector

F = 0.3048
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "ph_assets")
K = (21.0 - 15.1667) / 35.0
zr = lambda fy: 21.0 - (35 - fy) * K

PLACE = {
    # model: (decimate ratio, [(x, fy, z, rot, variant), ...])
    "sofa_02": (1.0, [(31.6, 25.6, 0, 90, None), (8.75, 4.6, 10.333, 0, None)]),
    "modern_coffee_table_01": (0.5, [(34.6, 25.6, 0, 0, None), (8.75, 8.5, 10.333, 90, None)]),
    "mid_century_lounge_chair": (0.6, [(36.0, 21.6, 0, -138, None)]),
    "bar_chair_round_01": (0.25, [(32.9, fy, 0, 90, None) for fy in (9.3, 11.1, 12.9)]),
    "hanging_industrial_lamp": (0.5, [(30.05, fy, 11.4, 0, None) for fy in (9.0, 11.2, 13.4)]),
    "ceiling_fan": (0.3, [(5.0, 8.0, 8.95, 0, None), (5.5, 27.0, 8.95, 20, None),
                          (34.4, 25.6, 13.0, 10, None), (11.0, 28.0, zr(28.0) - 0.2, 0, None)]),
    "potted_plant_02": (0.5, [(38.3, 31.8, 0, 30, None), (73.0, 33.0, 0, 0, None), (2.6, 2.6, 10.333, 70, None)]),
    "potted_plant_04": (0.35, [(29.2, 10.5, 3.0, 0, None), (20.6, 23.4, 3.0, 40, None), (53.3, 19.5, 3.0, 0, None)]),
    "modern_arm_chair_01": (0.6, [(14.5, 8.5, 10.333, -90, None), (12.6, 11.5, 0, -90, None)]),
    "ceramic_vase_01": (0.3, [(60.5, 17.0, 3.05, 0, None)]),
    "ceramic_vase_02": (0.3, [(63.5, 16.4, 3.05, 0, None)]),
    "ceramic_vase_03": (0.3, [(66.5, 17.8, 3.05, 0, None)]),
    "covered_car": (0.6, [(80.6, 14.0, 0, 180, None)]),
    "metal_tool_chest": (0.4, [(88.1, 22.8, 0, -90, None)]),
    "shrub_02": (1.0, [(56.0, 37.9, -0.5, 0, 0), (66.0, 37.9, -0.5, 40, 1), (75.0, 37.7, -0.5, 80, 2),
                        (85.5, 37.9, -0.5, 10, 3), (-2.6, 10.0, -0.5, 0, 1), (-2.6, 22.0, -0.5, 60, 3),
                        (45.8, 30.0, -0.5, 0, 0)]),
}


def import_model(name):
    path = glob.glob(os.path.join(ASSETS, name, "*.gltf"))[0]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = []
    for o in new:
        if o.type == "MESH":
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
            meshes.append(o)
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    return meshes


def decimate(o, ratio):
    if ratio >= 0.999:
        return
    mod = o.modifiers.new("dec", "DECIMATE")
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def run(collection="Mehnert"):
    col = bpy.data.collections[collection]
    placed = []
    for name, (ratio, spots) in PLACE.items():
        base = import_model(name)
        for o in base:
            if o.data.users > 1:
                o.data = o.data.copy()
            decimate(o, ratio)
        # each variant is centered on its own XY so it lands exactly at the placement point
        centers = []
        for o in base:
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            centers.append(Vector(((min(p.x for p in pts) + max(p.x for p in pts)) / 2,
                                   (min(p.y for p in pts) + max(p.y for p in pts)) / 2, 0)))
        for (x, fy, z, rot, variant) in spots:
            T = Matrix.Translation(Vector((x * F, (35 - fy) * F, z * F))) @ Matrix.Rotation(math.radians(rot), 4, "Z")
            items = list(enumerate(base)) if variant is None else [(variant, base[variant])]
            for i, o in items:
                c = o.copy()
                shift = Matrix.Translation(-centers[i]) if variant is not None else Matrix.Identity(4)
                c.matrix_world = T @ shift @ o.matrix_world
                col.objects.link(c)
                placed.append(c)
        for o in base:
            for uc in list(o.users_collection):
                uc.objects.unlink(o)
    # shrink furniture textures for the web
    for img in bpy.data.images:
        if img.filepath and "ph_assets" in bpy.path.abspath(img.filepath) and max(img.size) > 512:
            img.scale(512, 512)
    # join everything into one object for a single lightmap atlas
    for o in placed:
        o.data = o.data.copy()
    active = placed[0]
    with bpy.context.temp_override(active_object=active, object=active,
                                   selected_objects=placed, selected_editable_objects=placed):
        bpy.ops.object.join()
    active.name = "LM_furn"
    active.data.name = "LM_furn"
    # glTF imports name their texture UV map "UVMap" already; make sure it is first
    return active


if __name__ == "__main__":
    run()
