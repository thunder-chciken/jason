"""Mehnert Home barndominium, modeled from the 10.08.26 construction documents
(Greg James Designs, sheets A1-A5). Dimensions in feet; see lib.py for axes."""
import bpy, math, os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
importlib.reload(lib)
from lib import prism, box, cyl, pcyl, solid_wall, Y, flush

K = (21.0 - 15.1667) / 35.0                      # 2:12 roof slope
zr = lambda x, y: 21.0 - y * K                   # house roof underside (high at front)
zs = lambda x, y: 18.833 - y * K                 # studio/garage roof underside
zb = lambda x, y: 12.4 - (y - 17.0) * (1.3 / 15.3)  # breezeway roof
zp = lambda x, y: 10.1 + y * (1.25 / 8.5)        # porch roof (y negative)
T, S = 0.75, 0.1                                 # exterior wall, outer skin


# ---------------------------------------------------------------- helpers
def pbox(axis, a0, a1, c0, c1, z0, z1, mat, col=True):
    if axis == "x":
        prism(mat, a0, a1, c0, c1, z0, z1, col)
    else:
        prism(mat, c0, c1, a0, a1, z0, z1, col)


def ext_walls(x0, x1, y0, y1, top, ops, skin="rpanel", sides="SNWE"):
    g = lambda k: ops.get(k, [])
    if "S" in sides:
        solid_wall(skin, "x", x0, x1, y0, y0 + S, 0, top, g("S"))
        solid_wall("drywall", "x", x0 + S, x1 - S, y0 + S, y0 + T, 0, top, g("S"), base="c1")
    if "N" in sides:
        solid_wall(skin, "x", x0, x1, y1 - S, y1, 0, top, g("N"))
        solid_wall("drywall", "x", x0 + S, x1 - S, y1 - T, y1 - S, 0, top, g("N"), base="c0")
    if "W" in sides:
        solid_wall(skin, "y", y0 + S, y1 - S, x0, x0 + S, 0, top, g("W"))
        solid_wall("drywall", "y", y0 + T, y1 - T, x0 + S, x0 + T, 0, top, g("W"), base="c1")
    if "E" in sides:
        solid_wall(skin, "y", y0 + S, y1 - S, x1 - S, x1, 0, top, g("E"))
        solid_wall("drywall", "y", y0 + T, y1 - T, x1 - T, x1 - S, 0, top, g("E"), base="c0")


def window(axis, s, e, sill, head, c_out, c_in, style="twin", ext_trim="trim"):
    """c_out = outside face coordinate, c_in = inside face coordinate."""
    d = 1 if c_in > c_out else -1               # direction pointing inside
    cf = c_out + d * 0.3
    fr = (cf - 0.15, cf + 0.15)
    w = 0.18
    for (a0, a1, z0, z1) in ((s, s + w, sill, head), (e - w, e, sill, head),
                             (s, e, head - w, head), (s, e, sill, sill + w)):
        pbox(axis, a0, a1, *fr, z0, z1, "trim")
    m = (s + e) / 2
    if style == "twin":
        pbox(axis, m - 0.08, m + 0.08, *fr, sill, head, "trim")
        zm = (sill + head) / 2
        pbox(axis, s, e, cf - 0.08, cf + 0.08, zm - 0.06, zm + 0.06, "trim")
    elif style == "dh":
        zm = (sill + head) / 2
        pbox(axis, s, e, cf - 0.08, cf + 0.08, zm - 0.06, zm + 0.06, "trim")
    elif style == "casement":
        pbox(axis, m - 0.08, m + 0.08, *fr, sill, head, "trim")
    pbox(axis, s, e, cf - 0.01, cf + 0.01, sill, head, "glass", True)
    # exterior trim (proud of the wall) and interior casing
    o0, o1 = sorted((c_out, c_out - d * 0.06))
    tw = 0.35
    for (a0, a1, z0, z1) in ((s - tw, s, sill - 0.1, head + tw), (e, e + tw, sill - 0.1, head + tw),
                             (s - tw, e + tw, head, head + tw), (s - tw - 0.1, e + tw + 0.1, sill - 0.25, sill)):
        pbox(axis, a0, a1, o0, o1, z0, z1, ext_trim, False)
    i0, i1 = sorted((c_in, c_in + d * 0.05))
    for (a0, a1, z0, z1) in ((s - 0.25, s, sill, head + 0.25), (e, e + 0.25, sill, head + 0.25),
                             (s - 0.25, e + 0.25, head, head + 0.25), (s - 0.35, e + 0.35, sill - 0.25, sill)):
        pbox(axis, a0, a1, i0, i1, z0, z1, "trim", False)
    s0, s1 = sorted((c_in, c_in + d * 0.3))
    pbox(axis, s - 0.3, e + 0.3, s0, s1, sill - 0.06, sill, "trim", False)


def leaf(thin, t0, t1, w0, w1, z0, z1, mat, style, latch, col):
    """A real door leaf: stiles, rails and recessed panels on both faces, plus lever handles.
    thin: world axis through the leaf thickness ('x' or 'y'); t0..t1 thickness; w0..w1 width;
    style 'int' (two recessed panels) or 'ext' (glass upper lite over two panels); latch: width
    coordinate of the latch edge."""
    if w1 < w0:
        w0, w1 = w1, w0

    def part(a, b, za, zb, ta, tb, m, solid=col):
        if thin == "x":
            prism(m, ta, tb, a, b, za, zb, solid)
        else:
            prism(m, a, b, ta, tb, za, zb, solid)

    st, top, bot = 0.36, 0.36, 0.72
    lock0, lock1 = z0 + 2.95, z0 + 3.55
    inset = 0.035
    # frame at full thickness
    part(w0, w0 + st, z0, z1, t0, t1, mat)
    part(w1 - st, w1, z0, z1, t0, t1, mat)
    part(w0 + st, w1 - st, z1 - top, z1, t0, t1, mat)
    part(w0 + st, w1 - st, z0, z0 + bot, t0, t1, mat)
    part(w0 + st, w1 - st, lock0, lock1, t0, t1, mat)
    # lower panel, recessed on both faces, with a raised field
    part(w0 + st, w1 - st, z0 + bot, lock0, t0 + inset, t1 - inset, mat)
    part(w0 + st + 0.12, w1 - st - 0.12, z0 + bot + 0.12, lock0 - 0.12, t0 + inset * 0.4, t1 - inset * 0.4, mat, False)
    if style == "ext":
        mid = (t0 + t1) / 2
        part(w0 + st, w1 - st, lock1, z1 - top, mid - 0.012, mid + 0.012, "glass")
        for (a, b, za, zb) in ((w0 + st, w1 - st, lock1, lock1 + 0.05), (w0 + st, w1 - st, z1 - top - 0.05, z1 - top),
                               (w0 + st, w0 + st + 0.05, lock1, z1 - top), (w1 - st - 0.05, w1 - st, lock1, z1 - top)):
            part(a, b, za, zb, t0 - 0.02, t1 + 0.02, mat, False)                # glazing stops
    else:
        part(w0 + st, w1 - st, lock1, z1 - top, t0 + inset, t1 - inset, mat)
        part(w0 + st + 0.12, w1 - st - 0.12, lock1 + 0.12, z1 - top - 0.12, t0 + inset * 0.4, t1 - inset * 0.4, mat, False)
    # lever handles on both faces
    lx = latch - 0.22 if abs(latch - w1) < abs(latch - w0) else latch + 0.22
    zc = z0 + 3.05
    for (ta, tb, ra, rb) in ((t0 - 0.05, t0, t0 - 0.03, t0), (t1, t1 + 0.05, t1, t1 + 0.03)):
        part(lx - 0.07, lx + 0.07, zc - 0.07, zc + 0.07, ra, rb, "black", False)  # rose
        lever0, lever1 = (lx, lx + 0.38) if lx < latch else (lx - 0.38, lx)
        lever0, lever1 = (lx - 0.38, lx) if latch > lx else (lx, lx + 0.38)
        part(min(lever0, lever1), max(lever0, lever1), zc - 0.025, zc + 0.025, ta, tb, "black", False)


def door(axis, s, e, head, c0, c1, hinge="s", swing=1, leaf="door_int", open_=True,
         glass=False, casing=(True, True), z0=0.0, pocket=False):
    j = 0.08
    for (a0, a1, zz0, zz1) in ((s, s + j, z0, head), (e - j, e, z0, head), (s, e, head - j, head)):
        pbox(axis, a0, a1, c0, c1, zz0, zz1, "trim", False)
    w = e - s - 2 * j
    th = 0.15
    if pocket:
        pass                                    # pocket door: the leaf is slid away inside the wall
    elif open_:
        h = s + j if hinge == "s" else e - j
        a0, a1 = (h, h + th) if hinge == "s" else (h - th, h)
        f = c1 if swing > 0 else c0
        thin = "x" if axis == "x" else "y"
        style = "ext" if leaf == "door_ext" else "int"
        globals()["leaf"](thin, a0, a1, f, f + swing * w, z0 + 0.03, head - j, leaf, style, f + swing * w, False)
    else:
        cm = (c0 + c1) / 2
        if glass:
            for (a0, a1, zz0, zz1) in ((s + j, s + j + 0.25, z0, head - j), (e - j - 0.25, e - j, z0, head - j),
                                       (s + j, e - j, head - j - 0.25, head - j), (s + j, e - j, z0, z0 + 0.6)):
                pbox(axis, a0, a1, cm - th / 2, cm + th / 2, zz0, zz1, leaf, True)
            mid = (s + e) / 2
            pbox(axis, mid - 0.08, mid + 0.08, cm - th / 2, cm + th / 2, z0, head - j, leaf, True)
            pbox(axis, s + j, e - j, cm - 0.01, cm + 0.01, z0 + 0.6, head - j - 0.25, "glass", True)
        else:
            thin = "y" if axis == "x" else "x"
            style = "ext" if leaf == "door_ext" else "int"
            latch = e - j if hinge == "s" else s + j
            globals()["leaf"](thin, cm - th / 2, cm + th / 2, s + j, e - j, z0 + 0.03, head - j, leaf, style, latch, True)
    for side, c in zip(casing, (c0, c1)):
        if not side:
            continue
        dd = -1 if c == c0 else 1
        k0, k1 = sorted((c, c + dd * 0.05))
        for (a0, a1, zz0, zz1) in ((s - 0.29, s, z0, head + 0.29), (e, e + 0.29, z0, head + 0.29),
                                   (s - 0.29, e + 0.29, head, head + 0.29)):
            pbox(axis, a0, a1, k0, k1, zz0, zz1, "trim", False)


def garage_door(s, e, head, c_out, c_in):
    d = 1 if c_in > c_out else -1
    cf = c_out + d * 0.35
    fr = sorted((cf - 0.1, cf + 0.1))
    cols, rows = 4, 4
    for i in range(cols + 1):
        a = s + (e - s) * i / cols
        pbox("x", a - 0.12, a + 0.12, *fr, 0, head, "alum")
    for r in range(rows + 1):
        z = head * r / rows
        pbox("x", s, e, *fr, max(0, z - 0.12), min(head, z + 0.12), "alum")
    pbox("x", s, e, cf - 0.02, cf + 0.02, 0, head, "glass_frost")


def rail(axis, a0, a1, c, zbase, h=3.0, zfn=None, mat="black"):
    """Black metal guard rail. zfn(a) overrides a sloped base (stairs)."""
    base = (lambda a: zbase) if zfn is None else zfn
    n = max(2, int((a1 - a0) / 0.33))
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        z = base(a)
        r = 0.08 if i in (0, n) else 0.035
        pbox(axis, a - r, a + r, c - r, c + r, z, z + h, mat)
    if zfn is None:
        pbox(axis, a0, a1, c - 0.12, c + 0.12, zbase, zbase + h + 0.15, "colonly")
        pbox(axis, a0, a1, c - 0.1, c + 0.1, zbase + h, zbase + h + 0.15, mat)
        pbox(axis, a0, a1, c - 0.05, c + 0.05, zbase + 0.3, zbase + 0.38, mat)
    else:
        # sloped top rail: one prism whose top/bottom follow the stair pitch
        za, zb_ = base(a0), base(a1)
        lin = lambda t: za + (zb_ - za) * (t - a0) / (a1 - a0)
        if axis == "y":
            prism("colonly", c - 0.12, c + 0.12, a0, a1, lambda x, y: lin(y), lambda x, y: lin(y) + h + 0.15)
            prism(mat, c - 0.1, c + 0.1, a0, a1, lambda x, y: lin(y) + h, lambda x, y: lin(y) + h + 0.15)
        else:
            prism(mat, a0, a1, c - 0.1, c + 0.1, lambda x, y: lin(x) + h, lambda x, y: lin(x) + h + 0.15)


def can(x, fy, z):
    """Recessed downlight."""
    pcyl("light", x, fy, z - 0.02, z, 0.22, 16, False)


# ---------------------------------------------------------------- site
prism("grass", -160, 250, -150, 200, -0.6, -0.5, True, skip="b")
prism("gravel", 74, 92, 38.5, 200, -0.5, -0.47, True, skip="b")        # drive to garage doors
prism("gravel", 52, 92, 35, 38.5, -0.5, -0.47, True, skip="b")         # apron at rear doors
prism("concrete_ext", 27.4, 31.4, -60, -8, -0.5, -0.45, True, skip="b")  # front walk

# ---------------------------------------------------------------- slabs & floors
prism("concrete_ext", 0, 40, 0, 35, -1.33, 0, True)                 # house slab
prism("concrete_ext", 51.625, 89.625, 0, 35, -1.33, 0, True)        # studio + garage slab
prism("concrete_ext", 40, 51.625, 17, 32.3, -1.33, 0, True)         # breezeway slab
prism("concrete_ext", 0, 40, -8, 0, -1.33, -0.08, True)             # front porch

prism("oak", T, 40 - T, T, 35 - T, 0, 0.02, True, skip="b")
box("tile", 15.3, 21.08, 4.75, 16.3, 0, 0.04, True, skip="b")       # master bath
box("tile", 15.25, 21.08, 21.0, 29.9, 0, 0.04, True, skip="b")      # hall bath
box("concrete", 15.3, 21.08, T, 4.4, 0, 0.04, True, skip="b")       # mech
prism("concrete", 51.625 + T, 89.625 - T, T, 35 - T, 0, 0.02, True, skip="b")
prism("tile", 40, 51.625, 17.3, 32.0, 0, 0.03, True, skip="b")      # breezeway
box("tile", 52.4, 56.95, 27.2, 34.25, 0.02, 0.04, True, skip="b")   # half bath

# ---------------------------------------------------------------- house shell
house_ops = {
    "S": [(4.0, 8.5, 2, 7), (27.8, 30.9, 0, 7), (32.4, 36.9, 2, 7),
          (2.75, 8.75, 13.3, 17.55), (12.25, 18.25, 13.3, 17.55),
          (21.75, 27.75, 13.3, 17.55), (31.25, 37.25, 13.3, 17.55)],
    "N": [(3.6, 8.0, 2, 7), (15.6, 18.7, 0, 7), (30.6, 35.6, 3.4, 7.9)],
    "W": [(5.5, 9.9, 2, 7), (3.0, 6.0, 13.2, 17.9)],
    "E": [(27.2, 30.3, 0, 7)],
}
ext_walls(0, 40, 0, 35, zr, house_ops)
for (s, e) in ((4.0, 8.5), (32.4, 36.9)):
    window("x", s, e, 2, 7, 0, T, "twin")
for (s, e) in ((2.75, 8.75), (12.25, 18.25), (21.75, 27.75), (31.25, 37.25)):
    window("x", s, e, 13.3, 17.55, 0, T, "fixed", "cedar")
window("x", 3.6, 8.0, 2, 7, 35, 35 - T, "twin")
window("x", 30.6, 35.6, 3.4, 7.9, 35, 35 - T, "casement")
window("y", 5.5, 9.9, 2, 7, 0, T, "twin")
window("y", 3.0, 6.0, 13.2, 17.9, 0, T, "dh", "cedar")
door("x", 27.8, 30.9, 7, 0, T, hinge="e", swing=1, leaf="door_ext")          # front door (open)
door("x", 15.6, 18.7, 7, 35 - T, 35, hinge="s", leaf="door_ext", open_=False)  # mech, closed
door("y", 27.2, 30.3, 7, 40 - T, 40, hinge="e", swing=-1, leaf="door_ext")      # to breezeway

# vaulted ceiling under the roof
prism("drywall", T, 40 - T, T, 35 - T, lambda x, y: zr(x, y) - 0.12, zr, False)

# roof: dark standing seam over white soffit, white fascia
prism("trim", -1, 41, -1, 36, zr, lambda x, y: zr(x, y) + 0.42, True)
prism("roof", -1.05, 41.05, -1.05, 36.05, lambda x, y: zr(x, y) + 0.42, lambda x, y: zr(x, y) + 0.5, False)

# ---------------------------------------------------------------- house interior walls (plan coords)
def iw(x0, x1, fy0, fy1, ops=(), top=9.0, axis=None):
    """Interior partition; openings given in plan units along the long axis."""
    ax = axis or ("x" if (x1 - x0) > (fy1 - fy0) else "y")
    if ax == "x":
        solid_wall("drywall", "x", x0, x1, Y(fy1), Y(fy0), 0, top, ops, base="both")
    else:
        conv = [(Y(e), Y(s), sill, head) for (s, e, sill, head) in ops]
        solid_wall("drywall", "y", Y(fy1), Y(fy0), x0, x1, 0, top, conv, base="both")


iw(14.8, 15.3, T, 16.3, [(10.1, 13.1, 0, 6.67)])                 # bedroom | bath
iw(21.08, 21.58, T, 16.3)                                        # bath | kitchen
iw(15.3, 21.08, 4.4, 4.75)                                       # mech | bath
iw(T, 25.1, 16.3, 16.7, [(3.7, 6.9, 0, 7.33), (11.2, 14.2, 0, 6.67)])
iw(9.95, 10.3, 16.7, 22.5)
iw(T, 10.3, 22.2, 22.55)
iw(10.3, 21.4, 20.6, 21.0, [(11.2, 14.2, 0, 6.67), (15.5, 18.6, 0, 6.67)])
iw(21.4, 25.0, 20.6, 21.0, top=7.5)                              # under the stair run
iw(14.7, 15.25, 21.0, 35 - T, [(30.6, 33.6, 0, 6.67)])
iw(21.08, 21.4, 21.0, 35 - T)
iw(15.25, 21.08, 29.9, 30.25)

# interior doors (left open)
door("y", Y(13.1), Y(10.1), 6.67, 14.8, 15.3, pocket=True)                    # master bath pocket door
door("x", 3.7, 6.9, 7.33, Y(16.7), Y(16.3), hinge="s", swing=1)              # master closet
door("x", 11.2, 14.2, 6.67, Y(16.7), Y(16.3), hinge="e", swing=1)            # master bedroom
door("x", 11.2, 14.2, 6.67, Y(21.0), Y(20.6), hinge="s", swing=-1)           # bedroom 2
door("x", 15.5, 18.6, 6.67, Y(21.0), Y(20.6), hinge="e", swing=-1)           # hall bath
door("y", Y(33.6), Y(30.6), 6.67, 14.7, 15.25, hinge="s", swing=1)           # bedroom 2 closet

# ---------------------------------------------------------------- loft floor, stair, rails
box("drywall", T, 26.3, T, 17.6, 9.0, 10.3, True)
box("drywall", T, 21.4, 17.6, 35 - T, 9.0, 10.3, True)
box("oak", T, 26.3, T, 17.6, 10.3, 10.333, True, skip="b")
for (x0, x1, f0, f1) in ((T, T + 0.045, T, 35 - T), (T, 26.3, T, T + 0.045), (T, 21.4, 35 - T - 0.045, 35 - T)):
    box("trim", x0, x1, f0, f1, 10.333, 10.71, False)                       # loft baseboards
box("oak", T, 21.4, 17.6, 35 - T, 10.3, 10.333, True, skip="b")
box("trim", 26.3, 26.4, T, 17.6, 9.0, 10.333, False)                # loft edge fascia
box("trim", 21.3, 26.4, 17.6, 17.7, 9.0, 10.333, False)

RISE = 10.333 / 18
box("oak", 25.92, 26.84, 30.5, 34.0, 0, RISE, True)                  # step 1
box("oak", 25.0, 25.92, 30.5, 34.0, 0, 2 * RISE, True)               # step 2
box("oak", 21.4, 25.0, 30.5, 34.25, 0, 3 * RISE, True)               # landing
TREAD = (30.5 - 17.6) / 14
for k in range(4, 18):
    fy0, fy1 = 30.5 - (k - 3) * TREAD, 30.5 - (k - 4) * TREAD
    top = k * RISE
    bottom = 0 if k <= 13 else top - 0.45
    box("oak", 21.4, 25.0, fy0, fy1, bottom, top, True)
for k in range(14, 18):                                              # stringer under floating treads
    fy0, fy1 = 30.5 - (k - 3) * TREAD, 30.5 - (k - 4) * TREAD
    box("drywall", 24.9, 25.05, fy0, fy1, k * RISE - 1.1, k * RISE - 0.45, False)
rail("y", Y(17.6), Y(0.9), 26.3, 10.333)                            # loft edge over kitchen/living
rail("x", 24.9, 26.3, Y(17.65), 10.333)
rail("y", Y(34.2), Y(17.6), 21.35, 10.333)                          # beside stairwell
stair_top = lambda a: min(17 * RISE, 3 * RISE + max(0.0, a - Y(30.5)) / TREAD * RISE)
rail("y", Y(30.5), Y(17.7), 25.05, 0, 3.0, zfn=stair_top)

# ---------------------------------------------------------------- kitchen
def base_cab(x0, x1, fy0, fy1, top=3.0, mat="cabinet"):
    box(mat, x0, x1, fy0, fy1, 0, top - 0.12, True)
    box("quartz", x0 - 0.06, x1 + 0.06, fy0 - 0.06, fy1 + 0.06, top - 0.12, top, True)


def fronts(face, a0, a1, c, z0, z1, kind="base", mat="cabinet", n=None):
    """Shaker doors/drawers with black pulls on a cabinet face, in plan units.
    face: direction the fronts look ('n','s','e','w'); c: the face plane (fy for n/s, x for e/w);
    a0..a1: span along the face (x for n/s, fy for e/w)."""
    if face in "ns":
        axis, cw, d, A0, A1 = "x", Y(c), (1 if face == "n" else -1), a0, a1
    else:
        axis, cw, d = "y", c, (1 if face == "e" else -1)
        A0, A1 = sorted((Y(a0), Y(a1)))

    def slab(p0, p1, zz0, zz1, t0, t1, m):
        pbox(axis, p0, p1, *sorted((cw + d * t0, cw + d * t1)), zz0, zz1, m, False)

    cols = n or max(1, round((A1 - A0) / 1.55))
    w = (A1 - A0) / cols
    if kind == "base":
        slab(A0, A1, z0, z0 + 0.33, 0, 0.004, "black")                       # shadowed toe kick
        rows = [(z0 + 0.36, z1 - 0.72, "door"), (z1 - 0.68, z1 - 0.16, "drawer")]
    elif kind == "upper":
        rows = [(z0 + 0.04, z1 - 0.04, "door")]
    else:
        rows = [(z0 + 0.36, z0 + 4.2, "door"), (z0 + 4.25, z1 - 0.05, "door")]
    for i in range(cols):
        p0, p1 = A0 + i * w + 0.012, A0 + (i + 1) * w - 0.012
        for (r0, r1, typ) in rows:
            fw = 0.19 if typ == "door" else 0.13
            slab(p0, p1, r0, r1, 0, 0.035, mat)                              # recessed centre panel
            for (q0, q1, s0, s1) in ((p0, p0 + fw, r0, r1), (p1 - fw, p1, r0, r1),
                                     (p0 + fw, p1 - fw, r1 - fw, r1), (p0 + fw, p1 - fw, r0, r0 + fw)):
                slab(q0, q1, s0, s1, 0.035, 0.07, mat)                       # rails and stiles
            if typ == "drawer":
                m = (p0 + p1) / 2
                zc = (r0 + r1) / 2
                slab(m - 0.27, m + 0.27, zc - 0.022, zc + 0.022, 0.07, 0.13, "black")
            else:
                x = p0 + 0.12 if i % 2 else p1 - 0.12
                zz = (r0 + 0.15, r0 + 0.7) if kind == "upper" else (r1 - 0.75, r1 - 0.2)
                slab(x - 0.022, x + 0.022, zz[0], zz[1], 0.07, 0.13, "black")


# rear run with an undermount sink: counter split around the basin opening
box("cabinet", 21.6, 32.2, T, 2.9, 0, 2.88, True)
box("cabinet", 34.2, 36.4, T, 2.9, 0, 2.88, True)
box("cabinet", 32.2, 34.2, T, 2.9, 0, 2.2, True)
for (x0, x1, f0, f1) in ((21.54, 32.2, T - 0.06, 2.96), (34.2, 36.46, T - 0.06, 2.96),
                         (32.2, 34.2, T - 0.06, 1.15), (32.2, 34.2, 2.4, 2.96)):
    box("quartz", x0, x1, f0, f1, 2.88, 3.0, True)
box("sinkdark", 32.2, 34.2, 1.15, 2.4, 2.2, 2.32, True)                    # basin floor
for (x0, x1, f0, f1) in ((32.2, 32.24, 1.15, 2.4), (34.16, 34.2, 1.15, 2.4),
                         (32.2, 34.2, 1.15, 1.19), (32.2, 34.2, 2.36, 2.4)):
    box("steel", x0, x1, f0, f1, 2.32, 2.99, False)                         # basin walls
pcyl("black", 33.2, 1.0, 3.0, 4.15, 0.05, 8, False)                         # gooseneck faucet
box("black", 33.15, 33.25, 1.0, 1.65, 4.05, 4.15, False)
box("black", 33.15, 33.25, 1.6, 1.68, 3.75, 4.15, False)
fronts("s", 23.6, 36.4, 2.9, 0, 2.88, "base")

base_cab(21.6, 23.6, 2.9, 13.1)                                             # west run
fronts("e", 2.9, 6.9, 23.6, 0, 2.88, "base")
fronts("e", 9.5, 13.1, 23.6, 0, 2.88, "base")
# freestanding range between the west-run cabinets
box("steel", 21.7, 23.7, 6.9, 9.5, 3.0, 3.05, False)                        # cooktop
for i in range(5):
    pcyl("black", 22.65, 7.25 + i * 0.5, 3.05, 3.08, 0.18, 12, False)
box("steel", 23.6, 23.68, 6.92, 9.48, 0.3, 2.98, False)                     # range front
box("screen", 23.68, 23.7, 7.25, 9.15, 1.05, 2.0, False)                    # oven window
box("steel", 23.7, 23.82, 7.2, 9.2, 2.3, 2.36, False)                       # oven handle
for i in range(5):
    box("black", 23.68, 23.76, 7.35 + i * 0.45, 7.5 + i * 0.45, 2.62, 2.77, False)   # knobs
box("black", 23.6, 23.62, 6.92, 9.48, 0, 0.3, False)
# chimney hood
box("steel", 21.58, 23.45, 7.0, 9.4, 5.75, 6.2, True)
box("steel", 21.58, 22.45, 7.7, 8.7, 6.2, 9.0, True)
# stainless French-door refrigerator
box("steel", 21.6, 23.85, 13.1, 16.25, 0, 7.0, True)
box("black", 23.85, 23.87, 13.12, 16.23, 0.3, 6.98, False)
for (f0, f1) in ((13.14, 14.66), (14.69, 16.21)):
    box("steel", 23.87, 23.98, f0, f1, 2.5, 6.95, False)
box("steel", 23.87, 23.98, 13.14, 16.21, 0.32, 2.46, False)                # freezer drawer
for fy in (14.45, 14.9):
    box("alum", 23.98, 24.12, fy - 0.03, fy + 0.03, 3.4, 6.2, False)        # door handles
box("alum", 23.98, 24.12, 13.6, 15.75, 2.12, 2.18, False)                   # drawer handle
# pantry tower and uppers with crown trim
box("cabinet", 36.4, 39.25, T, 3.6, 0, 7.5, True)
fronts("s", 36.4, 39.25, 3.6, 0, 7.5, "tall", n=2)
box("cabinet", 21.58, 30.4, T, 1.95, 4.5, 7.5, True)
box("cabinet", 21.58, 22.9, 1.95, 6.6, 4.5, 7.5, True)
box("cabinet", 21.58, 22.9, 9.8, 13.1, 4.5, 7.5, True)
fronts("s", 22.9, 30.4, 1.95, 4.5, 7.5, "upper")
fronts("e", 1.95, 6.6, 22.9, 4.5, 7.5, "upper")
fronts("e", 9.8, 13.1, 22.9, 4.5, 7.5, "upper")
box("cabinet", 21.58, 30.5, T, 2.07, 7.5, 7.75, False)
box("cabinet", 21.58, 23.02, 2.07, 6.6, 7.5, 7.75, False)
box("cabinet", 21.58, 23.02, 9.8, 13.1, 7.5, 7.75, False)
# subway tile backsplash
box("subway", 21.58, 30.6, T, T + 0.04, 3.0, 4.5, False)
box("subway", 30.6, 35.6, T, T + 0.04, 3.0, 3.4, False)
box("subway", 35.6, 36.4, T, T + 0.04, 3.0, 4.5, False)
box("subway", 21.58, 21.62, T + 0.04, 13.1, 3.0, 4.5, False)
box("subway", 21.58, 21.62, 6.6, 9.8, 4.5, 5.75, False)
# island: cabinets on the kitchen side, counter overhang for seating on the living side
box("cabinet", 28.0, 31.1, 7.7, 14.7, 0, 2.88, True)
box("quartz", 27.94, 32.2, 7.64, 14.76, 2.88, 3.0, True)
fronts("w", 7.7, 14.7, 28.0, 0, 2.88, "base")
for fy in (9.3, 11.1, 12.9):                           # bar stool footprints (models placed in furnish.py)
    pcyl("colonly", 32.9, fy, 0, 2.5, 0.8, 8)
for fy in (9.0, 11.2, 13.4):                           # pendant downrods; shades come from furnish.py
    pcyl("black", 30.05, fy, 11.4, zr(0, Y(fy)) - 0.12, 0.025, 6, False)

# ---------------------------------------------------------------- living room
box("rug", 30.0, 38.8, 20.4, 30.8, 0.02, 0.04, False)
box("colonly", 30.25, 32.95, 22.6, 28.6, 0, 2.3)              # sofa footprint
box("colonly", 33.6, 35.6, 23.6, 27.6, 0, 1.3)                # coffee table footprint
box("colonly", 34.6, 37.4, 20.2, 23.0, 0, 3.0)                # lounge chair footprint
box("walnut", 37.6, 39.15, 21.8, 30.0, 0, 2.0, True)           # media console
box("black", 38.95, 39.2, 23.55, 28.25, 4.15, 6.95, False)      # 65-inch TV, wall mounted
box("screen", 38.93, 38.95, 23.62, 28.18, 4.22, 6.88, False)
pcyl("colonly", 38.3, 31.8, 0, 2.8, 1.1, 8)                   # potted plant footprint

# ---------------------------------------------------------------- bedrooms
def bed(x0, x1, fy0, fy1, head_side):
    """Bed with headboard on head_side ('w' or 'n')."""
    box("walnut", x0, x1, fy0, fy1, 0, 1.2, True)
    box("linen", x0 + 0.1, x1 - 0.1, fy0 + 0.1, fy1 - 0.1, 1.2, 2.0, True)
    if head_side == "w":
        box("navy", x0 + 2.0, x1 + 0.05, fy0 + 0.05, fy1 - 0.05, 2.0, 2.15, False)   # duvet fold
        box("walnut", x0 - 0.2, x0, fy0 - 0.2, fy1 + 0.2, 0, 4.2, True)
        for f in (fy0 + 0.6, fy0 + (fy1 - fy0) / 2 + 0.2):
            box("linen", x0 + 0.2, x0 + 1.4, f, f + (fy1 - fy0) / 2 - 0.8, 2.0, 2.5, False)
    else:
        box("navy", x0 - 0.05, x1 + 0.05, fy0 + 2.0, fy1 + 0.05, 2.0, 2.15, False)
        box("walnut", x0 - 0.2, x1 + 0.2, fy0 - 0.2, fy0, 0, 4.2, True)
        for f in (x0 + 0.6, x0 + (x1 - x0) / 2 + 0.2):
            box("linen", f, f + (x1 - x0) / 2 - 0.8, fy0 + 0.2, fy0 + 1.4, 2.0, 2.5, False)


def nightstand(x0, x1, fy0, fy1):
    box("walnut", x0, x1, fy0, fy1, 0, 2.1, True)
    pcyl("linen", (x0 + x1) / 2, (fy0 + fy1) / 2, 2.1, 3.3, 0.35, 12, False)


bed(1.0, 8.0, 4.4, 11.0, "w")                     # master: king, head on west wall
nightstand(T, 2.2, 2.4, 4.0)
nightstand(T, 2.2, 11.4, 13.0)
box("rug", 3.0, 10.5, 3.0, 12.4, 0.02, 0.04, False)
box("walnut", 12.5, 14.75, 1.2, 6.0, 0, 3.2, True)  # dresser
bed(2.9, 8.5, 22.75, 29.6, "n")                   # bedroom 2: queen, head on north
nightstand(1.0, 2.6, 22.6, 24.2)
nightstand(8.8, 10.4, 22.6, 24.2)
for (x0, x1, fy0, fy1) in ((0.8, 9.9, 16.7, 18.2), (15.3, 21.0, 32.6, 34.2)):   # closet shelves
    box("trim", x0, x1, fy0, fy1, 5.4, 5.5, False)

# ---------------------------------------------------------------- bathrooms & mech
def toilet(x, fy, facing):
    dx, dy = {"s": (0, 1), "n": (0, -1), "w": (-1, 0), "e": (1, 0)}[facing]
    tx, ty = x - dx * 0.9, fy - dy * 0.9
    pcyl("porcelain", x, fy, 0, 1.3, 0.62, 18)
    if dx == 0:
        box("porcelain", tx - 0.85, tx + 0.85, ty - 0.35, ty + 0.35, 1.3, 2.6, True)
    else:
        box("porcelain", tx - 0.35, tx + 0.35, ty - 0.85, ty + 0.85, 1.3, 2.6, True)


def vanity(x0, x1, fy0, fy1, sinks, mirror_side, face=None):
    box("walnut", x0, x1, fy0, fy1, 0, 2.85, True)
    if face == "n":
        fronts("n", x0, x1, fy0, 0, 2.85, "base", "walnut")
    elif face in ("e", "w"):
        fronts(face, fy0, fy1, x1 if face == "e" else x0, 0, 2.85, "base", "walnut", n=2)
    box("quartz", x0, x1, fy0, fy1, 2.85, 3.0, True)
    for (sx, sf) in sinks:
        pcyl("porcelain", sx, sf, 3.0, 3.35, 0.65, 20)
        fx, ff = {"n": (sx, sf - 0.7), "s": (sx, sf + 0.7), "e": (sx + 0.6, sf), "w": (sx - 0.6, sf)}.get(mirror_side, (sx - 0.6, sf))
        pcyl("steel", fx, ff, 3.0, 3.9, 0.05, 8, False)
    if mirror_side == "s":
        box("mirror", x0 + 0.3, x1 - 0.3, fy1, fy1 + 0.04, 4.0, 7.0, False)
    elif mirror_side == "n":
        box("mirror", x0 + 0.3, x1 - 0.3, fy0 - 0.04, fy0, 4.0, 7.0, False)
    elif mirror_side == "e":
        box("mirror", x1, x1 + 0.04, fy0 + 0.3, fy1 - 0.3, 4.0, 7.0, False)


toilet(16.85, 6.2, "s")
box("porcelain", 18.6, 21.08, 5.0, 9.6, 0, 1.9, True)          # tub
vanity(15.3, 21.08, 14.5, 16.3, [(16.9, 15.3), (19.5, 15.3)], "s", face="n")
vanity(19.2, 21.08, 21.0, 24.0, [(20.1, 22.5)], "e", face="w")
toilet(19.8, 25.5, "w")
box("mosaic", 15.3, 20.0, 26.8, 29.9, 0.04, 0.12, True)         # shower base
box("glass", 15.3, 20.0, 26.75, 26.8, 0.12, 7.0, True)          # shower glass
pcyl("steel", 15.7, 28.3, 6.2, 6.5, 0.3, 12, False)
pcyl("porcelain", 18.15, 3.7, 0, 5.0, 0.75)                     # water heater
box("steel", 15.5, 16.8, 1.0, 3.6, 0, 5.5, True)                # furnace

# ---------------------------------------------------------------- loft furnishing
box("rug", 4.0, 16.0, 6.0, 16.0, 10.333, 10.35, False)
box("colonly", 5.8, 11.7, 3.25, 5.95, 10.333, 12.7)            # loft sofa footprint
box("colonly", 6.8, 10.7, 7.5, 9.5, 10.333, 11.7)              # loft coffee table
box("colonly", 13.0, 16.0, 7.1, 9.9, 10.333, 13.3)             # loft arm chair
box("colonly", 11.1, 14.1, 10.1, 12.9, 0, 3.3)                 # master bedroom arm chair
box("walnut", T, 2.0, 18.5, 28.0, 10.333, 16.3, True)           # bookshelf wall
for z in (11.5, 12.8, 14.1, 15.4):
    box("linen", 1.0, 2.05, 18.8, 27.7, z, z + 0.7, False)
box("walnut", 12.0, 18.0, 30.5, 33.0, 12.75, 12.9, True)        # desk under front windows
for (dx, df) in ((12.2, 30.7), (17.8, 30.7), (12.2, 32.8), (17.8, 32.8)):
    box("black", dx - 0.05, dx + 0.05, df - 0.05, df + 0.05, 10.333, 12.75, False)

# ceiling fans
# ceiling fans come from furnish.py; living-room and loft fans hang on downrods
pcyl("black", 34.4, 25.6, 13.0, zr(0, Y(25.6)) - 0.12, 0.04, 8, False)
for (x, fy) in ((3, 2.5), (11, 2.5), (3, 13.5), (11, 13.5), (17.5, 2.0), (18.2, 10.0),
                (3, 25), (10, 25), (3, 32), (10, 32), (18.2, 25), (12.2, 18.6), (17, 18.6),
                (5, 19.4)):
    can(x, fy, 9.0)

# ---------------------------------------------------------------- front porch
for x in (1.3, 14.06, 26.8, 39.5):
    box("cedar", x - 0.33, x + 0.33, 34.95 + 7.4, 34.95 + 8.0, -0.08, 8.0, True)
box("cedar", -0.3, 40.3, 42.3, 42.95, 8.0, 8.67, True)          # 6x8 beam
prism("cedar_tg", -0.5, 40.5, -8.5, 0, zp, lambda x, y: zp(x, y) + 0.28, True)
prism("roof", -0.55, 40.55, -8.55, 0, lambda x, y: zp(x, y) + 0.28, lambda x, y: zp(x, y) + 0.36, False)
prism("trim", -0.6, 40.6, -8.65, -8.5, lambda x, y: zp(x, y) - 0.15, lambda x, y: zp(x, y) + 0.4, False)
for x in (6.5, 33.5):
    can(x, 39.0, zp(0, -4.0) - 0.01)

# ---------------------------------------------------------------- breezeway
ext_walls(40, 51.625, 17.0, 32.3, zb, {
    "N": [(41.2, 45.6, 2.1, 6.9), (46.4, 50.6, 2.1, 6.9)],
    "S": [(40.3, 45.3, 0, 8), (46.0, 51.0, 0, 8)],
}, skin="rpanel_grey", sides="SN")
window("x", 41.2, 45.6, 2.1, 6.9, 32.3, 32.3 - T, "twin")
window("x", 46.4, 50.6, 2.1, 6.9, 32.3, 32.3 - T, "twin")
door("x", 40.3, 45.3, 8, 17.0, 17.0 + T, leaf="alum", open_=False, glass=True)
door("x", 46.0, 51.0, 8, 17.0, 17.0 + T, leaf="alum", open_=False, glass=True)
prism("drywall", 40, 51.625, 17 + T, 32.3 - T, lambda x, y: zb(x, y) - 0.12, zb, False)
prism("trim", 39.9, 51.7, 16.0, 33.3, zb, lambda x, y: zb(x, y) + 0.35, True)
prism("roof", 39.9, 51.7, 15.95, 33.35, lambda x, y: zb(x, y) + 0.35, lambda x, y: zb(x, y) + 0.42, False)
box("steel", 40.8, 42.8, 13.9, 15.6, 0, 3.2, True)              # washer / dryer
box("steel", 40.8, 42.8, 15.7, 17.4, 0, 3.2, True)
box("cabinet", 40.8, 42.6, 8.6, 12.4, 0, 3.0, True)             # storage cabinet
box("quartz", 40.75, 42.65, 8.55, 12.45, 3.0, 3.12, True)
box("walnut", 50.0, 51.3, 9.6, 16.5, 0, 1.5, True)              # bench
can(46, 10.0, zb(0, Y(10.0)) - 0.13)
can(46, 15.0, zb(0, Y(15.0)) - 0.13)

# ---------------------------------------------------------------- studio + garage shell
studio_ops = {
    "S": [(59.4, 63.9, 2, 7), (68.4, 72.9, 2, 7), (77.4, 81.8, 2, 7),
          (57.5, 63.9, 11.3, 14.6), (67.5, 73.9, 11.3, 14.6), (77.4, 83.8, 11.3, 14.6)],
    "N": [(53.6, 69.6, 0, 10), (70.6, 73.6, 0, 7), (76.8, 86.8, 0, 10)],
    "W": [(26.7, 29.3, 0, 7)],
    "E": [(28.9, 32.05, 0, 7), (14.7, 19.2, 2, 7), (5.2, 9.7, 2, 7)],
}
ext_walls(51.625, 89.625, 0, 35, zs, studio_ops)
for (s, e) in ((59.4, 63.9), (68.4, 72.9), (77.4, 81.8)):
    window("x", s, e, 2, 7, 0, T, "twin")
for (s, e) in ((57.5, 63.9), (67.5, 73.9), (77.4, 83.8)):
    window("x", s, e, 11.3, 14.6, 0, T, "fixed", "cedar")
for (s, e) in ((14.7, 19.2), (5.2, 9.7)):
    window("y", s, e, 2, 7, 89.625, 89.625 - T, "twin")
garage_door(53.6, 69.6, 10, 35, 35 - T)
garage_door(76.8, 86.8, 10, 35, 35 - T)
door("x", 70.6, 73.6, 7, 35 - T, 35, leaf="door_ext", open_=False)
door("y", 26.7, 29.3, 7, 51.625, 51.625 + T, hinge="s", swing=1, leaf="door_ext")   # breezeway -> studio
door("y", 28.9, 32.05, 7, 89.625 - T, 89.625, leaf="door_ext", open_=False)
solid_wall("drywall", "y", T, 35 - T, 74.2, 74.6, 0, zs, [(26.7, 29.3, 0, 7)], base="both")     # studio | garage
door("y", 26.7, 29.3, 7, 74.2, 74.6, hinge="e", swing=1)
prism("drywall", 51.625 + T, 89.625 - T, T, 35 - T, lambda x, y: zs(x, y) - 0.12, zs, False)
prism("trim", 50.625, 90.625, -1, 36, zs, lambda x, y: zs(x, y) + 0.42, True)
prism("roof", 50.575, 90.675, -1.05, 36.05, lambda x, y: zs(x, y) + 0.42, lambda x, y: zs(x, y) + 0.5, False)
# canopies over the rear doors
prism("roof", 52.6, 88.0, 35, 38.0, 11.0, 11.25, False)
prism("trim", 52.6, 88.0, 37.9, 38.05, 10.9, 11.3, False)
prism("roof", 14.4, 19.9, 35, 37.5, 8.6, 8.8, False)
prism("roof", 89.625, 92.1, 27.9, 33.05, 8.6, 8.8, False)

# half bath
iw(52.375, 57.3, 26.8, 27.2, top=8.5)
iw(56.95, 57.3, 27.2, 35 - T, [(30.7, 33.8, 0, 6.67)], top=8.5)
box("drywall", 52.375, 57.3, 26.8, 35 - T, 8.5, 8.67, True)
door("y", Y(33.8), Y(30.7), 6.67, 56.95, 57.3, pocket=True)
toilet(53.6, 32.6, "e")
vanity(52.4, 54.4, 27.4, 29.6, [(53.4, 28.5)], None, face="e")
box("mirror", 52.4, 52.44, 27.6, 29.4, 4.0, 6.8, False)

# studio fit-out: counter, sink, work table, wheels, shelving
base_cab(52.4, 54.5, 8.6, 26.6, 3.0, "walnut")
fronts("e", 8.6, 22.95, 54.5, 0, 2.88, "base", "walnut")
box("steel", 52.6, 54.3, 23.0, 25.5, 2.9, 3.02, True)           # industrial sink
box("steel", 52.6, 54.3, 23.0, 25.5, 0, 2.9, True)
box("steel", 52.7, 53.9, 10.4, 11.6, 3.0, 4.0, False)           # coffee maker
box("black", 52.6, 54.2, 15.6, 17.4, 3.0, 4.2, False)           # microwave
box("walnut", 59.5, 68.5, 15.0, 19.5, 2.85, 3.05, True)         # work table
for (dx, df) in ((59.8, 15.3), (68.2, 15.3), (59.8, 19.2), (68.2, 19.2)):
    box("black", dx - 0.12, dx + 0.12, df - 0.12, df + 0.12, 0, 2.85, True)
for (wx, wf) in ((60.5, 25.5), (66.0, 25.5)):                   # pottery wheels + stools
    box("steel", wx - 1.0, wx + 1.0, wf - 1.2, wf + 1.2, 0, 1.6, True)
    pcyl("steel", wx, wf, 1.6, 1.75, 0.6)
    pcyl("clay", wx, wf, 1.75, 2.3, 0.3)
    pcyl("walnut", wx, wf + 2.0, 1.4, 1.55, 0.5)
    pcyl("black", wx, wf + 2.0, 0, 1.4, 0.08, 8)
for i in range(3):                                              # display shelving on the garage wall
    f0 = 11.0 + i * 3.6
    box("walnut", 72.6, 74.2, f0, f0 + 3.3, 0, 0.15, True)
    for z in (1.6, 3.2, 4.8, 6.4):
        box("walnut", 72.6, 74.2, f0, f0 + 3.3, z, z + 0.1, True)
        for j in range(3):
            pcyl("clay", 73.4, f0 + 0.6 + j * 1.05, z + 0.1, z + 0.7 + 0.2 * ((i + j) % 2), 0.25, 12, False)
    for ff in (f0, f0 + 3.2):
        box("black", 72.6, 74.2, ff, ff + 0.1, 0, 7.0, True)
pcyl("steel", 72.7, 27.8, 0, 3.2, 1.2, 16)                      # kiln

# garage: a parked car silhouette and wall shelving
box("colonly", 77.6, 83.6, 6.8, 21.2, 0, 4.6)                 # covered car footprint
box("colonly", 87.4, 88.8, 21.6, 24.0, 0, 2.1)                 # tool chest footprint
pcyl("colonly", 73.0, 33.0, 0, 2.8, 1.1, 8)                    # studio plant
box("walnut", 86.8, 88.85, 8.5, 15.0, 0, 0.12, True)            # shelving
for ff in (8.5, 11.7, 14.9):
    box("black", 86.8, 88.85, ff, ff + 0.1, 0, 7.0, True)
for z in (2.0, 4.0, 6.0):
    box("walnut", 86.8, 88.85, 8.5, 15.0, z, z + 0.1, True)

for (x, fy) in ((57, 10), (65, 10), (57, 22), (65, 22), (70, 30), (80, 12), (80, 26)):
    can(x, fy, zs(0, Y(fy)) - 0.13)

# exterior barn lights
for (x, y, z) in ((14.0, 35.5, 8.0), (20.3, 35.5, 8.0), (75.0, 35.5, 10.5), (88.0, 35.5, 10.5),
                  (52.8, 35.5, 10.5), (69.9, 35.5, 10.5), (31.6, -0.3, 6.6)):
    cyl("black", x, y, z, z + 0.7, 0.12, 8, False)
    cyl("black", x, y, z - 0.25, z, 0.6, 16, False)
    cyl("light", x, y, z - 0.27, z - 0.25, 0.5, 16, False)

flush()
