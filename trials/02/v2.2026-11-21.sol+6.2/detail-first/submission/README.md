# Rope-wrapped anchor keychain

**Deliverables:** [editable CadQuery source](build.py) · [final STEP](final.step) ·
[top](top.png) · [oblique](oblique.png) · [verification output](verification.txt)

The unpainted design uses a 2.80 mm shaped backing, with the anchor raised 0.85 mm
and the rope raised 1.40 mm above it. The SVG's white rope halo becomes lowered
clearance where the rope passes the eye, crossbar and shank. The finished model
is 60.00 × 69.30 × 4.20 mm, with a Ø6.50 mm through-bore centered in the eye.

## First piece: the rope crossing

Without the rope-to-anchor gaps, the emblem would read as one merged relief
rather than a rope wrapped around an anchor. I built only the shank, stock and
rope crossing on a 34.65 × 25.77 mm piece of the backing, at the same scale and
relief heights as the final part. I exported and reopened [coupon.step](coupon.step)
and inspected its unpainted [top view](coupon-1to1.png) and
[oblique view](coupon-oblique.png) before building and exporting the full part.
The angled view separates the two tiers; the orthographic view shows the breaks
flanking the climbing rope. The full emblem and final backing had not yet been built.
The final coupon renders use the refined lighting also used for the full part.

The target-size view is tagged at 300 DPI. Print at **100% / actual size**, not
fit-to-page: the page image is approximately 42 mm square and its coupon
approximately 34.65 mm wide. Inspecting this raster digitally is not a
calibration of anyone's display and is not a physical print test. The other
renders have independent display scales.

## Verification and limits

- Both STEP files reimported as one valid solid. The coupon and final part both
  show anchor–gap–rope–gap–anchor across the shank centerline. The two gaps along
  that line measure approximately 1.14 and 1.12 mm from sampled solid occupancy
  (not the minimum clearance over the entire design).
- The reimported final bore has a full Ø6.50 mm circular edge at four elevations.
  A full-length Ø6.49 mm digital gauge clears the solid. The base retains an
  uninterrupted 2 mm radial collar around the bore through its sampled height.
  The raised art does not extend outside the backing footprint.
- The [same-scale diagnostic comparison](comparison.png) compares the original
  SVG rendered independently with the two top-elevation masks from the
  reimported STEP. At 8 samples per SVG unit, footprint intersection over union
  was 97.78% for the anchor and 96.92% for the rope. The coupon interior measured
  98.41% and 97.01%, respectively. The diagnostic colors are not part of the
  solid or its unpainted renders.
- A 66 mm width / Ø7.00 mm bore rebuild remained valid; the bore remained
  concentric with the eye while the relief heights stayed unchanged.

The SVG determines the relief centerlines, silhouette and crossing gaps.
The custom backing outline is not in the artwork; its 142-unit span sets the
60 mm overall width. Stroke offsets use interpolated curves; the white halo
is omitted wherever it would simply be blank backing. The Ø6.50 mm bore is
dimensioned independently instead of tracing the SVG's roughly Ø6.76 mm eye
opening. The rope is a smooth, blunt-ended band with no invented fiber texture
or literal undercuts. There are no modeled edge breaks. Ring fit, strength,
minimum printable feature size, and manufacturing tolerances were not tested.

## Rebuild

From the project root, using the supplied Python environment:

```sh
.venv/bin/python submission/build.py coupon
.venv/bin/python submission/build.py final
.venv/bin/python submission/verify.py
```

The builder uses CadQuery 2.8.0, NumPy, OpenCV, Pillow and VTK. The independent
mask comparison uses CairoSVG and the supplied `reference.svg`. Edit the
named dimensions and Bézier control points in `build.py` to change the model.
The STEP is exchange geometry, not a feature-history file.
