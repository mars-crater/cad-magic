# CAD Magic · Lesson 2 transfer trial

Two editable, millimetre-based reliefs built with CadQuery 2.8.0. The comparison panels put the original supplied image beside the independently reopened STEP at the same orthographic scale and orientation. The oblique cameras are separate proof views, not reference overlays.

## Madeira

[STEP](madeira.step) · [North-up top](madeira-top.png) · [Matched reference comparison](madeira-comparison.png) · [Unpainted oblique](madeira-oblique.png) · [Numerical checks](madeira-checks.json)

- **145 × 68.489 × 28 mm**. The XY scale is isotropic relative to the supplied raster. The underside is flat, the base datum is 3 mm, and the maximum added relief is 25 mm (5× a chosen shallow 5 mm rendition of the same normalized raster). The PNG supplies elevation ranks but no metres-per-grey-level calibration, so this is a design exaggeration, not a claimed ratio to a real-world vertical scale.
- Thresholded low intensities and closed small gaps to find the main island. Detached components were omitted. The outline is a generalized shoreline, not a surveyed coastline. A lightly blurred elevation raster was sampled on a 2.7-pixel-pitch interior grid and along the perimeter; constrained triangulation and a sewn closed shell produce actual planar CAD faces. Facets and simplified shoreline are visible by design.
- The north-up outline and slender east-pointing spur match the reference; the spur is more angular and the low far-eastern edge is uncertain in the dark raster. Projected STEP footprint IoU was **0.9707** for the main island and **0.9302** in the eastern peninsula crop, relative to the dominant original component above grayscale 2.
- The central high ground and descending valleys survive in the STEP. At source position (130,60), the central crest is **26.096 mm** above the underside; along the same column to the south, the sampled surface falls to **15.759** then **8.113 mm**. The south valley is **10.840 mm** versus its flanking **21.580 / 23.433 mm** banks; the north valley likewise falls below both its banks. **2,561** in-footprint matched raster/mesh samples gave Pearson **r = 0.9923**. The grayscale oblique makes the high ground, drainage faces and lower peninsula visible without elevation colors or material paint.

## Manchester United crest keychain

[STEP](crest.step) · [Front](crest-top.png) · [Matched reference comparison](crest-comparison.png) · [Unpainted oblique](crest-oblique.png) · [Numerical checks](crest-checks.json)

- The artwork is **60 mm** wide before adding its rim. The reimported part is **61.869 × 75.099 × 3.850 mm** including the loop. A **2.50 mm** backing supports a **0.65 mm** field and **1.35 mm** raised marks; both heights are measured above the backing. These are chosen emboss depths for planar artwork, not a physical-scale exaggeration. The normal view uses grayscale indexed to actual geometric height so the flat levels can be read head-on. It is not a paint specification.
- At matched scale the ship and masts, devil and trident, both footballs and their grooves, curved banners and both words are identifiable. The red devil is recessed relative to the high shield field. Raised gold-class footprint IoU was **0.9929** against the thresholded supplied PNG; approximate landmark windows ranged **0.9870–1.0000**. This measures mask registration, not readability at a physical viewing distance. The original color gradients and antialiasing were reduced to two actual heights; the contour tolerance drops or simplifies small details, and the backing broadens the perimeter and locally bridges separation between motifs. The oblique shows the depth transitions without height-coded paint.
- An **11 mm OD** ring is joined above the backing by a short tab. The reopened model has two analytic **5.000 mm** bore circles at **Z = 0 and 2.5 mm**, a clear vertical ray through the center and material immediately beyond the rim of the hole. The bore's lower edge sits **5.334 mm** above the supplied artwork's highest opaque pixel.

## Rebuild and verification

From the directory containing the supplied references:

```sh
.venv/bin/python submission/build.py both
.venv/bin/python submission/verify.py both --variants
```

[Build parameters and image tracing](build.py) · [Terrain shell conversion](terrain_mesh.py) · [Independent STEP verification/rendering](verify.py) · [Edit checks](variant-checks.json)

Each reopen returned one valid solid. The Madeira width edit from 145 to 160 mm kept overall height at 28 mm. Editing the bore from 5 to 6 mm kept the 11 mm outer ring and the concentric XY center unchanged. Those two edits were rebuilt and measured in memory; the submission STEP files are the nominal designs. Default outputs were visually inspected after rendering. No slicer, print, ring fit, or load test was performed. Polygonal edges and very fine crest marks are visible in the renders but their physical reproduction wasn't tested.

Development checks caught an invalid, self-touching gold contour from pixel tracing and a failed constrained triangulation of a raw coastline with repeated vertices. Both switched to subpixel marching-squares contouring before external review. A smooth-surface split prototype was cancelled before export because it did not produce a result in the initial run; the submitted terrain is explicitly faceted.

## Supplied references

- Madeira input: [Mapzen Terrarium, AWS Registry of Open Data](https://registry.opendata.aws/terrain-tiles/); brief bounds west −17.30°, east −16.62°, north 32.90°, south 32.61°.
- Crest input: supplied raster of the [Manchester United FC emblem](https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg); reference only, not covered by the project MIT license. The comparison is part of the local trial, not for publication.
