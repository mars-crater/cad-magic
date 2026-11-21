# Lesson 2: Splines and Sketch Pictures

I reviewed [Andy Eskenazi's Session 2 outline](https://github.com/andyeske/How-to-CAD-Almost-Anything#S2) and [slides](https://github.com/andyeske/How-to-CAD-Almost-Anything/blob/main/Session%20Files/Session%202/Session%202.pdf), especially slides 2 and 4–6. MIT OpenCourseWare's [How to CAD Almost Anything](https://ocw.mit.edu/courses/res-16-002-how-to-cad-almost-anything-january-iap-2024/) uses SolidWorks; I practiced the technique in CadQuery. I did not review the recording.

A sketch picture gives you a tracing reference, not a real-world scale. Set an origin and calibrate from a known length before tracing. Use enough spline points to preserve significant changes in curvature, but don't chase every pixel. A periodic spline makes the seam smooth; check that the resulting profile closes and doesn't cross itself before extruding.

- [Terrain](terrain.step): I made an original [synthetic contour image](contour-reference.png), set the scale at 5 px/mm, traced 24 points per contour, and extruded three 3 mm levels. This is a tracing exercise, not surveyed terrain. The ray sampler assumes each contour has a single outer boundary along rays from the common center; hand-trace more complex outlines instead.
- [Keychain](keychain.step): I used eight authored points for a smooth outline and treated the 5 mm through-hole as a separate feature so its diameter does not depend on the silhouette.

Both STEP reimports were valid single solids. I checked terrain height (9 mm) and decreasing sectional areas at the three levels, plus keychain thickness (4 mm), bore diameter (5 mm), and an interior section through the bore. No print was tested.

[Editable source](models.py) · [Render from the exported STEP geometry](renders.png)

Rebuild with `python models.py` in an environment with CadQuery and Pillow.
