# Anchor keychain

Rebuild from the assignment directory: `.venv/bin/python submission/model.py`. The editable inputs are model.py and reference.svg. The STEP is the resulting single solid, not a parametric feature history.

Only overall width (60 mm) was specified. I chose a rounded plaque, with the SVG eyelet center as the attachment point. The shank, crossbar, flukes and eye stand 1.0 mm proud of a 2.8 mm base; the rope stands 1.6 mm proud. White clearance beside the rope becomes a lower strip of exposed base so the crossings read without paint. The eye aperture in the relief surrounds a separate 4.4 mm through-bore. The source viewBox maps at 60/146 mm per unit about (80,84), with Y flipped.

The STEP reopened as one valid 60.000 × 68.219 × 4.400 mm solid. Cross-sections rasterized in the source frame overlap the source artwork by 98.82% IoU at z=3.3 mm (all artwork), and 96.58% at z=4.1 mm (rope alone). The comparison uses the supplied SVG, not the renders. A centered 4.398 mm cylindrical probe passes through without solid overlap. Rebuilding with a 5 mm bore retained its center and the 60 mm width. See checks.json for measured rim positions.

Both orthographic views show the reimported STEP, using the same scale and one material; dark outlines are display edges, not paint. Source curves are approximated with simplified raster contours; subpixel fragments are discarded. No physical print, strength test, keyring fit test, or tolerance allowance is verified.
