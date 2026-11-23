# Six-wing spinner — editable exterior study

This model follows the **right-hand CAD screenshot** in the supplied `reference.png`, not the photographed circular spinner on the left. The screenshot has no dimensions or calibrated view. This is a visual reconstruction, not a trace, an original feature tree, or a mechanical design.

## Files and rebuild

- `spinner.py`: editable CadQuery source. Millimetres; XY is the rotor plane, Z is the hub axis, and the origin is on that axis at the wing mid-plane.
- `spinner.step`: colored STEP assembly with named parts. It does not carry CadQuery history.
- `top.png` and `oblique.png`: orthographic renders tessellated from the exported STEP, including its component colors. Both 1600 × 1200 images use the same scale (132 mm vertically); the oblique camera foreshortens the rotor plane.
- `render_step.py` regenerates the two views. `verify_step.py` checks the nominal build, imports the delivered STEP, and separately rebuilds and exports a parameter variant. `verification.txt` records the run.

From this folder:

```sh
/tmp/cad-magic-venv/bin/python spinner.py
/tmp/cad-magic-venv/bin/python render_step.py spinner.step
/tmp/cad-magic-venv/bin/python verify_step.py spinner.step
```

The chosen scale is **approximately 122 mm across the opposing outer tip rods**, with a **60 mm blade tip station**, **41 mm maximum hub width across flats**, and **26.8 mm crown diameter**. These are design choices, not dimensions read from the supplied image. Change the tip station and crown diameter with `--tip` and `--cap-radius`, change the symmetry with `--arms`, or edit the dimensioned profile stations in the source; use `--output` to save a variant separately.

## Visual comparison to the supplied screenshot

| Landmark visible on the right | Model and inspection view |
| --- | --- |
| Six silver radial wings on a beveled, dark-edged hexagonal center | Top view shows six 60° sectors, including the last-to-first gap; the oblique view shows the separate light deck and dark frame surfaces. |
| Wings broaden toward a curled end with a rounded crosswise rod and narrow transverse bands | Top shows the slightly swept outline and rounded tip bars; oblique shows the raised ends and three modeled blind grooves per wing. |
| Cylindrical housings hang to one side beneath each wing, with a dark/open mouth | Oblique shows the offset hollow nacelles and several visible mouths, while the top view makes the consistent handedness easy to see. |
| Raised orange center inside a notched/detail ring and two circles of small accents | Top shows the concentric organization, six lobes and two rows of gold inlays. Oblique shows the crown rise and shallow top circular groove. |

The oblique camera was selected to put the upper arm leaning right and show open nacelles under the right and lower-right arms, as in the screenshot. This is a landmark comparison, not a fitted camera or quantified image overlay. The screenshot does not establish exact wing sweep, underside detail, nacelle section, color, layer thicknesses or the number and depth of the small details; those features were interpreted.

## Verification scope

The verifier checks positive-volume valid solids, nominal dimensions, the cylindrical crown axis, the repeated component positions, and the gap around the pattern seam. Point probes check that each wing groove opens while leaving a floor, that each nacelle has open bore stations and a retained wall, and that the deck seats retain material beneath the pins. The rebuild changes six sectors to five, the tip station from 60 to 64 mm, and the crown diameter from 26.8 to 25.2 mm, then repeats those checks before and after STEP export.

This is a multipart visual assembly, not a collision-free or fused manufacturing model. The blade roots and mounts intentionally enter their adjacent volumes at joints. No hidden bearing, balance, spin clearance, material selection, structural analysis, printability, or manufacturing fits were inferred or validated.
