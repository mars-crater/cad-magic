# CAD transfer trial — incomplete / failed verification

## Rebuild

From the trial root, Python 3.12: `python3 -m venv .venv && .venv/bin/pip install cadquery opencv-python-headless cairosvg matplotlib`, then `.venv/bin/python submission/scripts/build.py` and `.venv/bin/python submission/scripts/verify_render.py`. Inputs are `inputs/madeira.png` and `inputs/cad-magic-mufc.svg`; the latter is a reference for this exercise, not licensed by this project. The scripts use CadQuery/OpenCascade and raster contour tracing. STEP is a geometric export, not editable feature history; the scripts are editable.

## Design and result

- Madeira: a 120 × 60.73 mm sea plate, 2 mm thick, and nine 0.65 mm relative-luminance terraces; maximum overall height 7.85 mm. This is not a calibrated DEM: input brightness was treated as monotonic relative elevation, not metres. No physical vertical-exaggeration factor can be established from these inputs. North is +Y. Coastline and peninsula are derived from the raster, but the oblique render has obvious spurious long triangles and an overly fragmented surface; valleys and central high ground are not reliably represented. **Fail** visual relief criterion. No quantitative source-to-STEP contour sections were completed.
- Crest: 60 mm diameter round backing, 2 mm thick, nominal emblem height 55 mm, red regions 0.35 mm and yellow regions 0.8 mm above base, with a 12 mm outside / 6 mm bore loop centered at (0,34) mm. This simplifies original colors into two heights and fills/loses fine details. Top render suggests banner lettering and both footballs, but the ship and devil are faint and the lower lettering is obscured by triangulation artifacts; **fail** recognizability criterion. The loop lies outside the emblem and a 5.8 mm diameter through-cylinder probe intersects zero volume after STEP import, but this alone does not establish a valid single-piece attachment.

## Independent STEP checks and critical limitations

`verify_render.py` imports each STEP afresh and produces `results/verification.json` and renders from imported tessellation. Madeira reports 18 solids, bounding box 120 × 60.7287 × 7.85 mm, `isValid=False`. Crest reports 72 solids, bounding box 60 × 70 × 2.8 mm, `isValid=False`. The deliberately preserved overlapping contour solids were not fused and some traced profiles are invalid. These are **failed CAD deliverables**, not manufacture-ready models. Bounding boxes and bore probe do not override invalidity. No parameter variation/invariant test, slicer test, or physical print was completed. The rendered triangular artifacts also prevent confident inspection of source-aligned geometry. Corrective work would require robust contour topology/holes, boolean fusion to a valid single solid, geometry and parameter checks, reimport, and matched source/STEP section comparison.

## Artifacts

- `scripts/build.py`, `scripts/verify_render.py`: editable generator and independent importer/renderer.
- `results/*.step`, `results/*.log`, `results/verification.json`: preserved attempted exports and checks.
- `renders/*-top.png`, `renders/*-oblique.png`: matching views from reimported geometry, no color texture.
