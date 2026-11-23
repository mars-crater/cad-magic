# Lower-right wing unit

Visual estimate in millimetres; no scale or dimensions were supplied. The editable model is `model.py` (CadQuery 2.8); `wing.step` is its exported geometry. Rebuild with `/tmp/cad-magic-venv/bin/python model.py`, then regenerate the STEP-based views and checks with `verify_render.py`.

Reference comparison: the unit grows outward from the hub-side root; its pod lies underneath the inboard/middle wing, projects forward across the leading edge, and points along the chord. The rail crosses the outboard tip. The two outboard divisions are shallow cuts. The hub and other wings are excluded.

STEP reimport yielded four valid solids (wing, rail, nacelle, pylon); dimensions and volumes appear in `verification.txt`. A 120 mm span rebuild remained valid and placed the rail center at x=122 mm, preserving the 2 mm tip offset. The oblique and top PNGs are generated from reimported STEP geometry; the oblique rendering has triangulation shading artifacts on the flat wing. The design is a simplified approximation: the reference wing appears smoothly crowned and swept with shaped panel transitions and a more contoured nacelle, whereas this model uses a flat tapered slab, simple slots and a cylindrical pod. Attachment overlaps are not fused, and mechanical fit, printability, and true dimensions are unverified.
