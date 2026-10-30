# Mehnert Home 3D walkthrough

An interactive 3D walkthrough of the Mehnert Home barndominium, prepared by
Story Remodeling & Restoration, (918) 955-6234. The model is built from the
10.08.26 construction documents by Greg James Designs (sheets A1 to A5).

Visitors can:

- take a guided tour that moves from room to room on its own, with Next and Back buttons
- walk around freely: click or tap the floor to walk there, drag to look around,
  or use W A S D / arrow keys (there's a joystick on phones)
- jump to any room from the buttons along the top, or click the floor plan in the corner
- orbit around the outside of the house

## Hosting

`public/` is a static site with no build step. `vercel.json` points Vercel at it.

To deploy on Vercel: **Add New → Project → import this repo**. Leave the framework
preset on **Other** and deploy. Every push to `main` redeploys.

## What's in `public/`

| File | What it is |
| --- | --- |
| `index.html` | The viewer (three.js 0.165, loaded from jsDelivr) |
| `model/mehnert.json` | glTF scene with its meshopt-compressed geometry inlined |
| `model/lm_*.jpg` | Lighting baked in Cycles (lightmaps), one per area |
| `model/*.jpg, *.png` | Material and furniture textures |
| `model/sky.jpg` | Sky background |
| `model/bake.json` | Lightmap exposure and sky rotation the viewer reads |

## Rebuilding the model (`blender/`)

You need Blender 5.2 or newer and an NVIDIA GPU for the bake (a CPU works, just slower).

```bash
python blender/ph_download.py ph_assets     # CC0 furniture, textures and sky from polyhaven.com
python blender/make_textures.py             # procedural textures (already committed in blender/tex)
blender -b --factory-startup --python blender/bake.py -- 512 1.0
python blender/package.py
```

`bake.py` builds the house from the plan dimensions in `model.py`, places the
furniture from `furnish.py`, bakes the lightmaps and exports to
`blender/site/model/`. `package.py` inlines the geometry so the model is one
JSON file plus images. Copy `blender/site/model/` into `public/model/` to update
the live site.

All dimensions in `model.py` are in feet and come straight from the plans.
Things the plans don't specify are placeholders: finishes, furniture and
lighting fixtures. The garage floor is shown at the same level as the house,
while the plans have it 2 ft lower.

## Credits

Furniture, plant and texture scans, and the sky HDRI, are CC0 from
[Poly Haven](https://polyhaven.com).
