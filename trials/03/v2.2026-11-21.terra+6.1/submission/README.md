# Six-wing spinner exterior study

Editable CadQuery source: `spinner.py`; interchange geometry: `spinner.step`; reimport-based images: `top.png`, `oblique.png`. `render_vtk.py` tessellates the saved STEP, with display colors assigned for illustration (not stored STEP materials). `verify_render.py` reimports STEP and writes `verification.json`.

## Assumptions and fidelity

Reference: the right-hand CAD image in the supplied `reference.png`; no dimensions or orthographic drawings are supplied. Chosen units are mm, with wing tip centre at radius 81 mm and a 23 mm hub apothem; the actual bounding box is approximately 164.8 × 149.22 × 15.23 mm. The choice is an arbitrary study scale, not a measured size. Six radial tapered wings, transverse grooves, tip bars, offset cylindrical nacelles, an angular hub and concentric domed/bolt-ring details were interpreted visually. Angles, proportions, hub details and nacelle connections are estimates, not trace-accurate reproductions. Wings are flat rather than airfoil-shaped; nacelles and angular hub are simplified. The ring holes are blind over the hub, and nacelle openings are blind. No underside detail, bearing, mechanism, fasteners or manufacturing tolerances are inferred. It is not a functional or print-ready design.

The STEP is a **compound of 29 solids**, not a single fused or interference-free assembly. Some elements overlap intentionally; physical attachment, clearance and manufacture are not verified. The editable feature definition is the Python source, not a STEP feature history. Parameters `WINGS`, `HUB_R` and `WING_END` are environment variables, in addition to literals editable in the script; not every decorative dimension scales automatically.

## Rebuild and evidence

```
cd /tmp/rotor-n83/submission
/tmp/cad-magic-venv/bin/python spinner.py
/tmp/cad-magic-venv/bin/python verify_render.py
/tmp/cad-magic-venv/bin/python render_vtk.py
```

CadQuery 2.8.0 exported and reimported the STEP with `isValid() == True`, 29 solids and bounds x ±82.4, y ±74.6105, z −5.5 to 9.73 mm. Wing centroid radii were all 48.996 mm, at 60° increments including the 300°-to-0° seam. `verification.json` contains the reimport results; validity does not establish no collisions. An independent parameter exercise using `WINGS=5`, export and reimport produced a valid 25-solid compound with centroid radii 48.9963 mm and angular positions 0°, 72°, 144°, 216°, 288° (including a 72° closing gap). This demonstrates the count-driven radial pattern, not visual fidelity or manufacturability. Both images were inspected after rendering from the STEP. The top/oblique camera uses parallel projection and the same parallel scale, but is not a dimensioned drawing.
