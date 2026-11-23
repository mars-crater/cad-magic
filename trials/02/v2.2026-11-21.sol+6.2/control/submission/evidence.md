# Anchor relief keychain

The supplied emblem becomes an unpainted, one-piece plaque. The anchor's eye centers the attachment hole. The eye, crossbar, shank and flukes are at the upper relief level; the rope is slightly lower, and the SVG's white clearance stays at the plaque surface. Both renders show the same geometry with a single material and lighting.

| Feature | Design (mm) |
|---|---:|
| Overall width × height × thickness | 60.00 × 66.00 × 4.10 |
| Base thickness | 3.20 |
| Plaque corner radius / edge roundover | 10.00 / 0.45 |
| Anchor / rope above base | 0.90 / 0.52 |
| Through-bore diameter | 5.50 |
| Through-bore center relative to plaque center | X 0.00, Y +24.70 |

## Verification

- CadQuery checked the fresh model and the reimported `final.step`: each contains one valid solid, and the reimported bounding box measures **60.00 × 66.00 × 4.10 mm**. The reimported coaxial cylindrical face measures **Ø5.50 mm** and runs from Z = 0 through the 3.20 mm base into the open center of the relief eye. Point checks at three base heights found void at the center and just inside the cylinder, and material just outside it.
- The checker rasterizes the **original** SVG at 800 × 900 px and compares its two visible colored regions with planar sections of the **reimported STEP** at the same datum and scale. The lower section (Z = 3.46 mm) contains both raised regions; the upper section (Z = 3.91 mm) contains the anchor only. Intersect-over-union is **99.41% anchor, 96.09% rope, 98.91% combined**. White/background pixels count as empty relief: raised geometry there reduces the overlap score.
- Rebuilding with a **5.00 mm** bore retained the bounding box and identical section masks at the verification resolution. The smaller bore is only a parameter check, not the delivered STEP.
- Both 1200 × 1200 PNGs were rendered from the reimported STEP and visually checked. The top view shows the rope clearance and anchor outline; the oblique view also shows the two relief heights and open bore. They are orthographic illustrations, not dimensioned drawings; foreshortening differs between views.

## Assumptions and limits

The rounded plaque, its proportions and relief heights, and the bore size are design choices; only overall width is specified in the brief. The SVG is mapped at 0.38 mm per viewBox unit using (80, 89) as the plaque center and a flipped Y axis. The relief follows visible pixels per SVG color; the contours are short straight segments approximating the rendered artwork, not editable CAD splines. Very small raster specks are discarded. The functional hole is an independently sized analytical cylinder, not the trace of the SVG eye. The geometry is verified, but no slicer, printed specimen, ring fit, or load test was checked.

## Artifacts and rebuild

- `build.py` — editable CadQuery source; adjust the `Design` parameters.
- `final.step` — exchange solid, without feature history.
- `top.png`, `oblique.png` — reimported STEP renders.

From the folder containing `reference.svg`, run `.venv/bin/python submission/build.py`. Tested with CadQuery 2.8.0, CairoSVG 2.9.1, OpenCV 5.1.0, NumPy 2.5.5, Pillow 13.0.0 and VTK 9.6.2 using offscreen rendering.
