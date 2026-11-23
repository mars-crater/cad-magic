# Banana — photo-to-CAD trial

**Editable source:** `banana.py` defines paired silhouette landmarks and closed spline cross-sections. The default export is `banana.step`; `banana-deeper.step` is the same loft with its depth ratio changed from 0.77 to 0.92. These STEP files contain solids, not feature history.

**Reference:** `Banana.jpg` is the only shape input. The stem cut, widening shoulder, concave top, convex belly, and tapered blossom end are traced from the side view. The stem cut center is the datum and the image is registered to the CAD XY plane. The photograph provides no physical scale or back view: 0.45 mm/pixel, the depth, and subdued lengthwise ridging are estimates. Cut ends are modeled as planar caps. The sticker is a graphic, not a hole or raised feature; the sticker, peel speckling and cast shadow are omitted. Color is visualization only, not part of the STEP.

## Rebuild and check

```sh
uv venv .venv
uv pip install 'cadquery==2.8.0' 'pillow==13.0.0' 'scipy==1.18.1'
.venv/bin/python trace.py
.venv/bin/python banana.py
.venv/bin/python banana.py --depth-ratio .92 --output banana-deeper.step
.venv/bin/python render.py
```

Both exports reimport as one valid positive-volume solid. Bounding dimensions (mm): default **174.375 × 103.725 × 33.110**, edited **174.375 × 103.725 × 39.557**; volumes 149501.572 and 178479.576 mm³, respectively. `render.py` checks that XY dimensions and the matched silhouette remain unchanged within tolerance while Z scales with the depth parameter. Raster silhouettes of default and edited STEP overlap at 99.80% IoU.

`banana-comparison.png` shows the original photo, registered STEP reimport render, and contour overlay on the same 488×488 projection with no independent rescaling. `banana-matched.png` is the standalone matched render; `banana-oblique.png` shows the loft with 30° tilt. The observed photo/STEP overlap is 98.09% IoU, relative to an approximate color mask with a manual separation of the contact shadow. This is a projected-profile check, not validation of the inferred 3D depth or actual physical size.
