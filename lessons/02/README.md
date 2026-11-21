# Lesson 2: Splines and Sketch Pictures

MIT IAP 2024 · RES.16-002, *How to CAD Almost Anything* · Andy Eskenazi · January 17, 2024

I reviewed the Session 2 outline and slides for the original SolidWorks track, then practiced in CadQuery. I did not review the recording or test a print.

## What I learned

A sketch picture gives you a tracing reference, not a real-world scale. Set an origin and calibrate from a known length before tracing. Use enough spline points to preserve significant changes in curvature, but don't chase every pixel. A periodic spline makes the seam smooth; check that the resulting profile closes and doesn't cross itself before extruding.

## Course exercises

The lesson uses a map to build topographic relief and a logo to make a keychain (slides 4–6). I used original practice artwork instead of the course examples.

## Practice results

- [Terrain](terrain.step): I made an original [synthetic contour image](contour-reference.png), set the scale at 5 px/mm, traced 24 points per contour, and extruded three 3 mm levels. This is a tracing exercise, not surveyed terrain. The ray sampler assumes each contour has a single outer boundary along rays from the common center; hand-trace more complex outlines instead.
- [Keychain](keychain.step): I used eight authored points for a smooth outline and treated the 5 mm through-hole as a separate feature so its diameter does not depend on the silhouette.

## Verification and limits

Both STEP reimports were valid single solids. I checked terrain height (9 mm) and decreasing sectional areas at the three levels, plus keychain thickness (4 mm), bore diameter (5 mm), and an interior section through the bore.

## Artifacts and rebuild

[Editable source](models.py) · [Render from the exported STEP geometry](renders.png)

After installing the repository requirements, run `python lessons/02/models.py` from the repository root.

## Sources

- [MIT OpenCourseWare course](https://ocw.mit.edu/courses/res-16-002-how-to-cad-almost-anything-january-iap-2024/)
- [Instructor's Session 2 outline](https://github.com/andyeske/How-to-CAD-Almost-Anything#S2)
- [Session 2 slides](https://github.com/andyeske/How-to-CAD-Almost-Anything/blob/main/Session%20Files/Session%202/Session%202.pdf), especially slides 2 and 4–6
- [Session recording](https://www.youtube.com/watch?v=4fcvDSAFNGo) (reference; not reviewed)
