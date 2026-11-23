# Rotary indexing dial

Millimetres. `dial.py` is the editable CadQuery source; `dial-8.step` is nominal and `dial-11.step` is the alternate. Only `--count` changes between exports. Origin is at the bottom centre, Z runs from 0 to 6; slot centres are on radius 23 and slot zero points along +X. Capsule length is overall, including the semicircular ends. The image is a tessellated view of the reimported nominal STEP; fine triangulation artifacts are rendering artifacts.

Rebuild and verify:

```sh
/tmp/cad-magic-venv/bin/python dial.py --count 8 --output dial-8.step
/tmp/cad-magic-venv/bin/python dial.py --count 11 --output dial-11.step
/tmp/cad-magic-venv/bin/python verify_render.py
```

## Evidence

Both STEP files were reimported in CadQuery 2.8.0: each is one valid solid with bounding box 64 × 64 × 6 mm. Their measured volumes are 18551.255033 mm³ (8) and 18382.843533 mm³ (11), matching the analytic disk-minus-bore-minus-capsules volumes to better than 0.00001 mm³. For every slot, point checks confirmed an opening at z=5, retained floor at z=3.9, material just beyond its width and length, and material at the next angular midpoint. The bore centre is empty at z=3. Pitch is 45° and 360/11° respectively, including the last-to-first gap. The source specifies the Ø8 through bore, 10 × 3 × 2 slot, and exact radial positions; the geometric tests sample rather than exhaustively measure every face. No manufacturing or printability validation was performed.
