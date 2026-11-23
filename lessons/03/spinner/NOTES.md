### Airfoil spinner study

[Instructor's outline](https://github.com/andyeske/How-to-CAD-Almost-Anything#S3) · [Slide 5](https://github.com/andyeske/How-to-CAD-Almost-Anything/blob/main/Session%20Files/Session%203/Session%203.pdf#page=5) · [Instructor's detailed reference view](https://github.com/andyeske/How-to-CAD-Almost-Anything/blob/main/Session%20Files/Session%203/Fidget%20Spinner.png). Reference media: Andy Eskenazi, MIT IAP 2024; linked, not redistributed.

The intended subject is the six-wing aircraft-inspired rotor on the **right** of slide 5, not the ring spinner on the left. Features selected before building: a faceted hub with a stepped circular cap; six swept airfoil wings; branched up/down tips; underwing engines with visible open intakes. The reference does not specify physical dimensions. This interpretation uses a 12 mm main chord, a symmetric analytic thickness distribution instead of tracing an unspecified airfoil, simplified tips and engine housings, and shallow hub pockets in place of the source trim. Panel markings and tip rods were omitted. The center is deliberately fused; this is an exterior form and pattern study, not a working bearing assembly.

[Editable model](model.py) · [Six-wing STEP](spinner.step) · [Render from STEP](spinner.png) · [Renderer](render.py)

From the repository root, with its requirements installed:

```sh
python lessons/03/spinner/model.py
python lessons/03/spinner/render.py
```

A single wing is lofted through parallel translated section planes; its hollow nacelle is revolved around a local chordwise axis before the entire wing assembly is copied around the hub. The hub crown revolves around the global axis instead. The angular pitch is 360° divided by count. The script also exports and reopens a temporary five-wing variant; it does not overwrite the six-wing artifact with that variant.

**Observed on both STEP imports:** one valid solid; maximum vertex radius 49.382 mm and overall height 14.700 mm. Equal 1 mm slices at radii 19–20 and 37–38 mm on the seed arm give equal sectional areas, 14.065 mm², outside the engine and compound tip. Every pattern position retains wing, engine wall, upper and lower tip material; a 4.2 mm diameter axial probe clears each entire engine, and halfway between successive arms the sampled span is empty. Five-way pitch is 72°, six-way pitch is 60°. Two orthographic views show the reimported six-wing surface; tones distinguish features, not materials. No physical spin, bearing fit, balance, aerodynamic behavior or print tested.
