"""Geometry builder for the Mehnert walkthrough model.

All inputs are in FEET. World axes: X east, Y north, Z up. The house front
(south) wall sits on Y=0. Plan helpers take "fy" = feet measured down from the
rear (north) wall on the drawings, and convert with Y = 35 - fy.

Faces are collected into lightmap groups (LM_house, LM_studio, LM_site), one
multi-material mesh each, so each group can get one baked lightmap atlas.
Transparent/emissive materials go to NOLM_* objects. Every face flagged solid
also goes into one invisible COLLIDER mesh the web viewer walks against.
"""
import bpy, bmesh, math, os

F = 0.3048
DEPTH = 35.0
HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "tex")
PBR = os.path.join(HERE, "tex_pbr")
M2FT = 1 / 0.3048

MATS = {
    # name: (color or texture file, tile_ft, roughness, metallic, alpha, emission)
    "rpanel":        ("pbr:rpanel_diff.jpg", 2.0 * M2FT, 0.45, 0.3, 1, 0),
    "rpanel_grey":   ("pbr:rpanel_grey_diff.jpg", 2.0 * M2FT, 0.45, 0.3, 1, 0),
    "drywall":       ("drywall.jpg", 4, 0.9, 0, 1, 0),
    "trim":          ((0.90, 0.90, 0.88), 4, 0.5, 0, 1, 0),
    "roof":          ("roof.jpg", 4, 0.55, 0.15, 1, 0),
    "concrete_ext":  ("pbr:concrete_ext_diff.jpg", 2.5 * M2FT, 0.85, 0, 1, 0),
    "concrete":      ("pbr:concrete_diff.jpg", 2.0 * M2FT, 0.4, 0, 1, 0),
    "oak":           ("pbr:oak_diff.jpg", 1.7 * M2FT, 0.5, 0, 1, 0),
    "tile":          ("tile.jpg", 4, 0.3, 0, 1, 0),
    "mosaic":        ("pbr:mosaic_diff.jpg", 2.0 * M2FT, 0.3, 0, 1, 0),
    "cedar":         ("cedar.jpg", 4, 0.6, 0, 1, 0),
    "cedar_tg":      ("pbr:cedar_tg_diff.jpg", 1.89 * M2FT, 0.6, 0, 1, 0),
    "grass":         ("pbr:grass_diff.jpg", 2.0 * M2FT, 0.95, 0, 1, 0),
    "gravel":        ("pbr:gravel_diff.jpg", 2.0 * M2FT, 0.95, 0, 1, 0),
    "glass":         ((0.70, 0.80, 0.86), 4, 0.05, 0, 0.22, 0),
    "glass_frost":   ((0.85, 0.88, 0.9), 4, 0.3, 0, 0.7, 0),
    "black":         ((0.04, 0.04, 0.045), 4, 0.4, 0.5, 1, 0),
    "steel":         ((0.72, 0.72, 0.72), 4, 0.28, 0.9, 1, 0),
    "alum":          ((0.32, 0.33, 0.34), 4, 0.35, 0.7, 1, 0),
    "cabinet":       ("cabinet.jpg", 4, 0.5, 0, 1, 0),
    "quartz":        ("quartz.jpg", 4, 0.2, 0, 1, 0),
    "porcelain":     ((0.95, 0.95, 0.94), 4, 0.12, 0, 1, 0),
    "fabric":        ("fabric.jpg", 2, 0.95, 0, 1, 0),
    "navy":          ("fabric_navy.jpg", 2, 0.95, 0, 1, 0),
    "rug":           ("rug.jpg", 6, 1.0, 0, 1, 0),
    "linen":         ((0.93, 0.92, 0.89), 4, 0.95, 0, 1, 0),
    "walnut":        ("pbr:walnut_diff.jpg", 2.0 * M2FT, 0.5, 0, 1, 0),
    "door_ext":      ((0.46, 0.21, 0.11), 4, 0.5, 0, 1, 0),
    "door_int":      ((0.93, 0.93, 0.91), 4, 0.45, 0, 1, 0),
    "light":         ((1.0, 0.95, 0.85), 4, 0.5, 0, 1, 6.0),
    "mirror":        ((0.85, 0.87, 0.9), 4, 0.04, 1.0, 1, 0),
    "screen":        ((0.02, 0.02, 0.025), 4, 0.15, 0, 1, 0),
    "clay":          ((0.72, 0.47, 0.32), 4, 0.8, 0, 1, 0),
    "plant":         ((0.22, 0.42, 0.2), 4, 0.8, 0, 1, 0),
    "carpaint":      ((0.18, 0.26, 0.34), 4, 0.25, 0.6, 1, 0),
    "colonly":       ((1.0, 0.0, 1.0), 4, 1.0, 0, 0.0, 0),
}
# normal map file and strength; roughness map file (same UV tiling as the albedo)
NORMALS = {"rpanel": ("rpanel_nor.jpg", 1.0), "rpanel_grey": ("rpanel_nor.jpg", 1.0),
           "drywall": ("plaster_nor.jpg", 0.12), "concrete_ext": ("concrete_ext_nor.jpg", 0.8),
           "concrete": ("concrete_nor.jpg", 0.5), "oak": ("oak_nor.jpg", 0.6), "mosaic": ("mosaic_nor.jpg", 0.8),
           "cedar_tg": ("cedar_tg_nor.jpg", 0.7), "grass": ("grass_nor.jpg", 1.0), "gravel": ("gravel_nor.jpg", 1.0),
           "walnut": ("walnut_nor.jpg", 0.5)}
ROUGHS = {"rpanel": "rpanel_rough.jpg", "rpanel_grey": "rpanel_rough.jpg", "concrete_ext": "concrete_ext_rough.jpg",
          "concrete": "concrete_rough.jpg", "oak": "oak_rough.jpg", "mosaic": "mosaic_rough.jpg",
          "cedar_tg": "cedar_tg_rough.jpg", "grass": "grass_rough.jpg", "gravel": "gravel_rough.jpg",
          "walnut": "walnut_rough.jpg"}

NOLM = {"glass", "glass_frost", "light", "mirror"}
SITE = {"grass", "gravel"}

GEO = {}
COL = {"v": [], "f": []}


def Y(fy):
    return DEPTH - fy


def _group(mat, pts):
    if mat in NOLM:
        return "NOLM_" + mat
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    if mat in SITE or cy < -8.6:
        return "LM_site"
    return "LM_house" if cx < 40.0 else "LM_studio"


def face(mat, pts, col=True):
    """pts: list of (x,y,z) feet, counter-clockwise seen from outside."""
    if col:
        i0 = len(COL["v"])
        COL["v"].extend((x * F, y * F, z * F) for (x, y, z) in pts)
        COL["f"].append(tuple(range(i0, i0 + len(pts))))
    if mat == "colonly":
        return
    b = GEO.setdefault(_group(mat, pts), {"v": [], "f": [], "uv": [], "mi": [], "mats": []})
    if mat not in b["mats"]:
        b["mats"].append(mat)
    tile = MATS[mat][1]
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = pts[0], pts[1], pts[2]
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    anx, any_, anz = abs(nx), abs(ny), abs(nz)
    i0 = len(b["v"])
    for (x, y, z) in pts:
        b["v"].append((x * F, y * F, z * F))
        if anz >= anx and anz >= any_:
            u, v = x, y
        elif any_ >= anx:
            u, v = x, z
        else:
            u, v = y, z
        b["uv"].append((u / tile, v / tile))
    b["f"].append(tuple(range(i0, i0 + len(pts))))
    b["mi"].append(b["mats"].index(mat))


def _ev(z, x, y):
    return z(x, y) if callable(z) else z


def prism(mat, x0, x1, y0, y1, z0, z1, col=True, skip=""):
    """Axis-aligned box in world feet. z0/z1 may be callables f(x,y) for sloped faces."""
    if x1 < x0: x0, x1 = x1, x0
    if y1 < y0: y0, y1 = y1, y0
    if x1 - x0 < 1e-4 or y1 - y0 < 1e-4:
        return
    b = {k: _ev(z0, *k) for k in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))}
    t = {k: _ev(z1, *k) for k in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))}
    p = lambda x, y, s: (x, y, s[(x, y)])
    if "b" not in skip: face(mat, [p(x0, y0, b), p(x0, y1, b), p(x1, y1, b), p(x1, y0, b)], col)
    if "t" not in skip: face(mat, [p(x0, y0, t), p(x1, y0, t), p(x1, y1, t), p(x0, y1, t)], col)
    if "s" not in skip: face(mat, [p(x0, y0, b), p(x1, y0, b), p(x1, y0, t), p(x0, y0, t)], col)
    if "n" not in skip: face(mat, [p(x1, y1, b), p(x0, y1, b), p(x0, y1, t), p(x1, y1, t)], col)
    if "w" not in skip: face(mat, [p(x0, y1, b), p(x0, y0, b), p(x0, y0, t), p(x0, y1, t)], col)
    if "e" not in skip: face(mat, [p(x1, y0, b), p(x1, y1, b), p(x1, y1, t), p(x1, y0, t)], col)


def box(mat, x0, x1, fy0, fy1, z0, z1, col=True, skip=""):
    """Plan-coordinate box (fy measured from the rear wall)."""
    prism(mat, x0, x1, Y(fy1), Y(fy0), z0, z1, col, skip)


def cyl(mat, cx, cy, z0, z1, r, seg=20, col=True, caps=True):
    """Vertical cylinder at world (cx, cy) feet."""
    pts = [(cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    for i in range(seg):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % seg]
        face(mat, [(xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1)], col)
    if caps:
        face(mat, [(x, y, z1) for (x, y) in pts], col)
        face(mat, [(x, y, z0) for (x, y) in reversed(pts)], col)


def pcyl(mat, cx, fy, z0, z1, r, seg=20, col=True):
    cyl(mat, cx, Y(fy), z0, z1, r, seg, col)


def solid_wall(mat, axis, a0, a1, c0, c1, z0, top, openings=(), col=True):
    """Wall along `axis` ('x' or 'y') from a0..a1, thickness c0..c1 on the other
    axis, from z0 to `top` (number or f(x,y)). openings: (s, e, sill, head)
    along the axis; overlapping openings at different heights are allowed."""
    pts = {a0, a1}
    for (s, e, _, _) in openings:
        if e > a0 and s < a1:
            pts.update((max(s, a0), min(e, a1)))
    pts = sorted(pts)
    for p, q in zip(pts, pts[1:]):
        if q - p < 1e-4:
            continue
        m = (p + q) / 2
        holes = sorted((sill, head) for (s, e, sill, head) in openings if s <= m <= e)
        z = z0
        spans = []
        for (sill, head) in holes:
            if sill > z + 1e-3:
                spans.append((z, sill))
            z = max(z, head)
        spans.append((z, None))
        for (lo, hi) in spans:
            zt = top if hi is None else hi
            if axis == "x":
                prism(mat, p, q, c0, c1, lo, zt, col)
            else:
                prism(mat, c0, c1, p, q, lo, zt, col)


def _mesh(name, verts, faces, uvs=None, mis=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bv = [bm.verts.new(v) for v in verts]
    uvl = bm.loops.layers.uv.new("UVMap") if uvs is not None else None
    for k, fidx in enumerate(faces):
        try:
            f = bm.faces.new([bv[i] for i in fidx])
        except ValueError:
            continue
        if mis is not None:
            f.material_index = mis[k]
        if uvl is not None:
            for loop, i in zip(f.loops, fidx):
                loop[uvl].uv = uvs[i]
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bm.to_mesh(me)
    bm.free()
    return me


def flush(collection_name="Mehnert"):
    col = bpy.data.collections.get(collection_name) or bpy.data.collections.new(collection_name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for gname, g in GEO.items():
        me = _mesh(gname, g["v"], g["f"], g["uv"], g["mi"])
        for m in g["mats"]:
            me.materials.append(get_mat(m))
        ob = bpy.data.objects.new(gname, me)
        col.objects.link(ob)
    me = _mesh("COLLIDER", COL["v"], COL["f"])
    ob = bpy.data.objects.new("COLLIDER", me)
    col.objects.link(ob)
    ob.hide_render = True
    ob.display_type = "WIRE"
    GEO.clear()
    COL["v"].clear()
    COL["f"].clear()


def _img(path, noncolor=False):
    img = bpy.data.images.load(path, check_existing=True)
    if noncolor:
        img.colorspace_settings.name = "Non-Color"
    return img


def get_mat(name):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    src, tile, rough, metal, alpha, emit = MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if isinstance(src, str):
        path = os.path.join(PBR, src[4:]) if src.startswith("pbr:") else os.path.join(TEX, src)
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = _img(path)
        tn.location = (-500, 300)
        nt.links.new(tn.outputs["Color"], p.inputs["Base Color"])
    else:
        p.inputs["Base Color"].default_value = (*src, 1)
    if name in ROUGHS:
        rn = nt.nodes.new("ShaderNodeTexImage")
        rn.image = _img(os.path.join(PBR, ROUGHS[name]), True)
        rn.location = (-500, 0)
        nt.links.new(rn.outputs["Color"], p.inputs["Roughness"])
    if name in NORMALS:
        f, strength = NORMALS[name]
        nn = nt.nodes.new("ShaderNodeTexImage")
        nn.image = _img(os.path.join(PBR, f), True)
        nn.location = (-700, -300)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = strength
        nm.location = (-300, -300)
        nt.links.new(nn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            m.blend_method = "BLEND"
    if emit:
        p.inputs["Emission Color"].default_value = (*src, 1)
        p.inputs["Emission Strength"].default_value = emit
    return m
