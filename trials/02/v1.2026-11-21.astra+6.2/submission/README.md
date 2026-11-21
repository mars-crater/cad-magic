# Lesson 2 — two single-material reliefs (private transfer trial)

Built from the provided Mapzen Terrarium north-up grayscale crop and supplied Manchester United emblem raster, with the frozen CAD Magic text (0357860). No course video, worked example, other submission, or external reference was used. The emblem is reference-only and is not covered by the project's MIT license. Nothing published.

## Rebuild

From the trial directory, run `.venv/bin/python submission/build.py madeira` and `.venv/bin/python submission/build.py crest`. Pass an optional final argument to change normalized terrain rise (default 15 mm) or bore diameter (default 4 mm). These commands replace the corresponding STEP. Run `.venv/bin/python submission/check.py madeira` and the same with `crest` for independent STEP readback, monochrome top and oblique PNGs, and JSON measurements. The checks assume the primary dimensions. Editable source is Python, not STEP feature history. CadQuery 2.8.0 / OCCT 7.9.3.1.1. Top is north-up/upright. Each model is independently fitted to its frame but its two views use the same orthographic scale. Depth-based shadows are display only.

## Madeira

Scale 0.55 mm per source pixel, positive y north, 2.5 mm nominal base; normalized source intensity 0–242 spans 15 mm of designed rise. This exaggeration is relative to grayscale, not asserted as a survey-calibrated vertical ratio. Three-pixel interior sample spacing and light smoothing reduce the realized peak. Reopened: one valid solid, **129.250 × 60.500 × 16.869 mm**. Rebuilding with a 10 mm normalized rise retained the footprint (see madeira-variant.txt).

- Coastline: recognizable, **partial**. West and south coast and the eastward taper correspond; tiny coves, coastal pixel slivers, and offshore fragments are not faithfully reproduced. The northeastern shoulder appears blunt. Boundary fan repair bridges some narrow coves.
- Eastern peninsula: **partial**. The narrow projection exists and points east; the last fine tip and islets are simplified.
- Central high ground: **pass**. Top view shows the high central spine between the drainage cuts; it rises well above the base in oblique.
- Descending valleys and unpainted depth: **pass with faceting**. Branching cuts run down both flanks, prominently toward the south. Steep faces and directional lighting separate them in oblique. Small tributaries are lost.
- Reopened mesh projected above the planes associated with source intensity 2/60/120/180 versus corresponding reference masks: pixel intersection-over-union **0.948 / 0.928 / 0.880 / 0.819** (1 = exact). Raster tests incorporate boundary rounding; they do not measure absolute geodetic error.

## Crest keychain

0.20 mm per emblem pixel. A flat convex backing connects the separated banners and balls; open negative spaces in the art thus become recessed fields, not holes. Backing 2.6 mm, chromatic field +0.65 mm, gold +1.45 mm from backing. These are intentional, nonphysical color-to-height exaggerations; gradients and other colors are not faithfully encoded. Thin curves are polygonally simplified. Reopened: one valid solid, **57.800 × 65.900 × 4.050 mm**.

- Ship: **partial**; the hull and three sails occupy the upper shield, but small spars do not stand out.
- Devil: **partial**; central negative relief and trident survive, but small limbs and the face are difficult to read.
- Footballs: **pass**; both circular forms and curved panel seams are present.
- Banners: **pass**; upper and lower arcs remain distinct, but convex backing changes their outside silhouette.
- Lettering: **partial**; the words MANCHESTER and UNITED can be followed in the top render, with some strokes weak under single-direction light. This is an enlarged digital inspection, not a physical-size legibility test.
- Attachment: **pass in CAD**; the round bore sits above the lettering and shield. Readback finds cylindrical faces of diameter **4.0 and 9.2 mm**, empty center at z = 0.1, 1.3, 2.5 mm, material at a 3.1 mm offset. The 5 mm bore rebuild retained the exterior dimensions and changed the void radius as intended (crest-variant.txt).
- Reference-mask agreement, including interior gaps: IoU **0.938** at z = 2.95 (chromatic area), **0.836** at z = 3.75 (gold). Both renders use the exported surfaces rather than a color decal.

## Failures and limits

Pre-submission attempts are retained in first-attempt/: an invalid spline intersection, a non-manifold faceted terrain, a topologically valid terrace whose high ground was missing, and invalid initial crest exports. The first flat-lit crest top render hid its detail; final renders use depth-derived contact shadows. None of those early exports is a deliverable. No remediation after independent reviewer feedback. No slicing, physical print, mechanical test, or licensing/publication claim.
