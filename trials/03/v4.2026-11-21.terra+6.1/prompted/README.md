# Spinner exterior study

A visually estimated, millimetre-scale interpretation of the **right-hand CAD design** in `../reference.png`; no dimensions were supplied. Six identical wings use 60° pitch, a 48 mm faceted hub, approximately 145 mm overall span, and 2.6 mm nominal wing section. Model source is `model.py`; the STEP is an assembly-like compound, not an editable feature-history file. Its 46 solids include overlapping decorative components; it is not a manufacturing assembly or a tested mechanism.

## Reference comparison and limits

The wing seed has a widening outline (15 to 19 mm), a thin section and an upturned outboard portion (center rises 5.2 mm). The reference has broad tapered wings with rounded raised tips, but its perspective and surface markings conceal the exact section; the seed is a simplified piecewise-loft approximation, not a measured or traced airfoil. The unadorned seed STEP and top/side images are included to expose this comparison. The model script exports that seed before constructing the repeated detailed assembly; the images were inspected after the initial full build, so this is not evidence that the comparison was completed before the first repeat. The hub is simplified: the reference has a domed cap, detailed perforated annulus and more complex facets; this model uses concentric low-profile cylinders and omits the perforations. Wing markings are raised strips, not engraved cuts. Nacelles are simple hollow tubes and the underside, bearings, fasteners and spin performance are not established by the image. Colors in renders are illustrative and assigned during rendering, not STEP material data.

## Verification and rebuild

From this directory:

```
/tmp/cad-magic-venv/bin/python model.py
/tmp/cad-magic-venv/bin/python verify_render.py
/tmp/cad-magic-venv/bin/python render_vtk.py
```

The verification script reimports the saved STEP and reports validity, solid count and bounding box in `checks.txt`. Nominal: 46 solids, valid compound, 145.202 × 135.749 × 15.704 mm. Seed: one valid solid, 52.5 × 19.5 × 8.3 mm. A separate `ARM_COUNT=5` rebuild exported and reimported as a valid 39-solid compound; the six-arm nominal was rebuilt afterward. Count changes pitch, not the station radii. No clearance, strength, tolerance, connectivity, printability or functional spinning test was performed. Top and oblique images are rendered from reimported nominal STEP with VTK; seed views use the reimported seed and independent display scales.
