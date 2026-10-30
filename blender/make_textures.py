"""Generate tileable 1024px textures for the Mehnert walkthrough model."""
import os, random
import numpy as np
from PIL import Image, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex")
os.makedirs(OUT, exist_ok=True)
N = 1024
rng = np.random.default_rng(7)


def noise(scale, octaves=4, seed=0):
    """Tileable value noise in [0,1]."""
    r = np.random.default_rng(seed)
    acc = np.zeros((N, N))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = scale * (2 ** o)
        g = r.random((s, s))
        img = Image.fromarray((g * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)
        # wrap-safe: tile 3x3 then crop center for seamless resize
        big = np.tile(g, (3, 3))
        img = Image.fromarray((big * 255).astype(np.uint8)).resize((N * 3, N * 3), Image.BICUBIC)
        a = np.asarray(img, dtype=float)[N:2 * N, N:2 * N] / 255.0
        acc += a * amp
        tot += amp
        amp *= 0.5
    return acc / tot


def save(name, arr):
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    Image.fromarray(arr).save(os.path.join(OUT, name), quality=88)


def rgb(base, var):
    return np.stack([base[i] + var for i in range(3)], -1)


# R-panel steel siding: 1024px = 4 ft wide, ribs every 12"
x = np.arange(N)
pos = (x % 256) / 256.0
shade = np.ones(N) * 0
rib = np.exp(-((pos - 0.5) ** 2) / 0.0012)        # major rib
minor = sum(np.exp(-((pos - p) ** 2) / 0.0002) for p in (0.17, 0.33, 0.67, 0.83))
prof = -18 * rib * np.sign(pos - 0.5) * 0.6 + 10 * rib - 4 * minor
col = np.tile(prof[None, :], (N, 1)) + noise(8, 3, 1) * 6
save("rpanel.jpg", rgb((236, 238, 238), col))

# Grey version for breezeway
save("rpanel_grey.jpg", rgb((176, 182, 186), col * 0.9))

# Standing seam roof (dark charcoal): seams every 16" -> 1024px = 4ft, 3 seams
pos = (x % 341) / 341.0
seam = np.exp(-((pos - 0.02) ** 2) / 0.00015)
prof = 30 * seam + noise(6, 3, 2)[0] * 0
col = np.tile(prof[None, :], (N, 1)) + noise(8, 3, 3) * 8
save("roof.jpg", rgb((52, 55, 58), col))

# White oak LVP floor: 1024px = 4ft, planks 7" wide (~150px), random lengths
img = np.zeros((N, N, 3))
pw = 146
grain = noise(4, 5, 5)
fine = np.asarray(Image.fromarray((rng.random((N, N)) * 255).astype(np.uint8)).resize((N // 16, N), Image.BILINEAR).resize((N, N), Image.BILINEAR), dtype=float) / 255
for i, x0 in enumerate(range(0, N, pw)):
    off = rng.integers(0, N)
    L = rng.integers(400, 900)
    for seg in range(3):
        tone = rng.normal(0, 5)
        y0 = (off + seg * L) % N
        ys = (np.arange(L) + y0) % N
        for c, b in enumerate((196, 168, 128)):
            img[ys[:, None], np.arange(x0, min(x0 + pw, N))[None, :], c] = b + tone
img += ((grain - 0.5) * 24 + (fine - 0.5) * 22)[..., None] * np.array([1, 0.9, 0.75])
for x0 in range(0, N, pw):
    img[:, x0:x0 + 2] *= 0.72
save("oak.jpg", img)

# Porcelain tile 24x24 (1024px = 4ft -> 2x2 tiles), warm grey
t = noise(6, 4, 9)
img = rgb((206, 202, 196), (t - 0.5) * 18)
for k in (0, 512):
    img[k:k + 4, :] = 150
    img[:, k:k + 4] = 150
save("tile.jpg", img)

# Small hex-ish mosaic for showers -> simple 3" square
t = noise(10, 3, 11)
img = rgb((232, 232, 230), (t - 0.5) * 10)
for k in range(0, N, 64):
    img[k:k + 3, :] = 185
    img[:, k:k + 3] = 185
save("mosaic.jpg", img)

# Polished concrete (1024px = 8ft)
t = noise(5, 6, 12)
sp = (rng.random((N, N)) > 0.995) * 25
save("concrete.jpg", rgb((168, 166, 160), (t - 0.5) * 40 + sp))

# Exterior concrete (rougher, lighter)
t = noise(7, 6, 13)
save("concrete_ext.jpg", rgb((196, 194, 188), (t - 0.5) * 34 + (rng.random((N, N)) - 0.5) * 14))

# Grass (1024px = 8ft)
t = noise(12, 6, 14)
blades = (rng.random((N, N)) - 0.5)
blades = np.asarray(Image.fromarray(((blades + 0.5) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), dtype=float) / 255 - 0.5
img = np.stack([78 + (t - .5) * 40 + blades * 40, 112 + (t - .5) * 50 + blades * 60, 52 + (t - .5) * 26 + blades * 20], -1)
save("grass.jpg", img)

# Gravel drive
t = noise(16, 4, 15)
g = rng.random((N, N))
g = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), dtype=float) / 255
save("gravel.jpg", rgb((150, 144, 134), (g - 0.5) * 90 + (t - .5) * 30))

# Cedar (posts, beams, trim, porch ceiling): grain along V, 1024px = 4ft
t = noise(3, 5, 16)
streak = np.asarray(Image.fromarray((rng.random((N, 64)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC), dtype=float) / 255
v = (streak - 0.5) * 40 + (t - 0.5) * 25
img = np.stack([186 + v, 124 + v * 0.8, 74 + v * 0.55], -1)
save("cedar.jpg", img)

# Porch ceiling tongue & groove (boards 5.5" ~ 117px along U)
img = np.stack([186 + v, 128 + v * 0.8, 80 + v * 0.55], -1).transpose(1, 0, 2).copy()
for k in range(0, N, 117):
    img[:, k:k + 3] *= 0.6
save("cedar_tg.jpg", img)

# Drywall: very subtle noise, off-white
t = noise(20, 3, 17)
save("drywall.jpg", rgb((240, 238, 233), (t - 0.5) * 6))

# Cabinet paint: soft sage
save("cabinet.jpg", rgb((118, 132, 118), (noise(20, 3, 18) - 0.5) * 6))

# Quartz counter: white with soft veins
t = noise(4, 6, 19)
vein = np.exp(-((np.sin((np.arange(N)[None, :] + t * 600) / 90.0)) ** 2) / 0.004) * 30
save("quartz.jpg", rgb((238, 236, 232), -vein + (t - 0.5) * 8))

# Fabric (sofa/bedding): woven oatmeal
w = np.add.outer(np.sin(np.arange(N) * 0.9), np.sin(np.arange(N) * 0.9)) * 4
save("fabric.jpg", rgb((196, 186, 168), w + (noise(30, 3, 20) - .5) * 14))
save("fabric_navy.jpg", rgb((56, 70, 96), w + (noise(30, 3, 21) - .5) * 12))

# Rug: muted pattern
t = noise(6, 4, 22)
yy, xx = np.mgrid[0:N, 0:N]
pat = ((np.sin(xx / 40.0) * np.sin(yy / 40.0)) > 0.3) * 18
save("rug.jpg", rgb((180, 164, 140), pat + (t - .5) * 20))

print("textures ->", OUT, sorted(os.listdir(OUT)))
