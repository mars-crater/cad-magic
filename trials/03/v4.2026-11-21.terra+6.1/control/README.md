# Spinner exterior study

A visual interpretation of the **right-hand** design in `../reference.png`, not the wheel on the left. Units are mm, chosen rather than measured: six arms on 60° pitch, nominal hub 56 mm across its circumscribed polygon and arm tip radius 65 mm. STEP bounding box is 133.00 × 123.68 × 18.80 mm (the transverse tip rails extend beyond the nominal tip radius). Hub centre and rotation axis are the origin and Z axis.

## Files and rebuild

- `model.py`: editable CadQuery construction with `ARMS` and `ARM_LENGTH` driving repeated geometry; remaining dimensions are explicit in source. It exports `spinner.step` beside itself.
- `spinner.step`: exported single solid; no editable feature history.
- `render.py`: reimports the saved STEP and tessellates it for `top.png` and `oblique.png`. Gold is a display-only convention, not a separate STEP material. Both use the same 140 mm view limits.
- `default-check.txt`, `variant-check.txt`: captured rebuild output.

Run from this directory:

```sh
/tmp/cad-magic-venv/bin/python model.py
/tmp/cad-magic-venv/bin/python render.py
# Variant check overwrites spinner.step; restore default afterward:
ARMS=5 ARM_LENGTH=70 /tmp/cad-magic-venv/bin/python model.py
/tmp/cad-magic-venv/bin/python model.py
```

## Evidence and limits

The default source and STEP reimport each reported one valid solid, volumes 35827.8234088 and 35827.8234101 mm³ respectively. The variant with five arms and 70 mm tip radius also rebuilt and reimported as one valid solid (34299.2469397 mm³). The pattern uses `360/N` and rotates each blade around the same origin, including last-to-first angular pitch; variant generation exercises this construction, but no independent measurement of each angular placement was made. Both renders were generated from the reimported default STEP. The oblique view was inspected; the radial blades, cap, tip rails, and underside pods are visible.

The reference is a perspective screenshot without dimensions or hidden views. Proportions and details are estimated, not a traced or dimensionally verified reproduction. This is a simplified monolithic exterior study: flat tapered blades substitute for curved surfaces, recessed lines and radial dimples are approximations, the housing and pods are simplified, and there is no bearing, rotating mechanism, separate assembly, manufacturing tolerance, or printability verification. Rendering is triangulated and may show facet artifacts; colors are illustrative. No claim is made that it spins or matches unseen geometry.
