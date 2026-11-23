# Rotary indexing dial — evidence

All dimensions are millimetres. `dial.py` is the editable CadQuery source; its only changed input between the two exports was the slot count.

Reproduce with `/tmp/cad-magic-venv/bin/python dial.py 8 dial_8.step` and the same command with `11 dial_11.step`. Run `verify_render.py` to reimport and check both STEP files; `render_step.py` renders the imported eight-slot STEP with VTK.

Reimport checks: both are valid single solids with bounding boxes 64 × 64 × 6 mm. Eight and eleven planar slot floors respectively were found at z=4, with their centers at radius 23 and angles 360i/count, and each floor area 28.068583 mm² (10 × 3 capsule). The nominal first floor center is (23, 0). Volumes are 18551.255033 and 18382.843533 mm³, matching the analytical disk-minus-through-bore-minus-slots calculation to displayed precision. Source specifies the 8 mm through bore, 10 × 3 mm overall slots, and 2 mm blind depth. The render is from the reimported eight-slot STEP.
