# Lower-right wing unit

Editable CadQuery source: `model.py`; exported geometry: `wing.step`. `oblique.png` and `top.png` are tessellated from the reimported STEP, not from a separate illustration. Rebuild with `/tmp/cad-magic-venv/bin/python model.py`, and regenerate/check with `verify_render.py`.

The image supplies no scale or dimensions. All dimensions are visual estimates in millimetres, with 180 mm wing span chosen as an arbitrary working scale. The model isolates the lower-right tapered wing, underwing hollow-front nacelle and pylon, and rounded tip rail; it excludes the hub and neighboring wings. Curvature, depth, wing section and hidden surfaces are inferred, not measured. The top is an orthographic CAD view, not a pixel-aligned comparison; only one perspective reference is available.

STEP reimport (CadQuery 2.8.0): five valid solids; overall bounding box 187.2 × 113.2 × 46.502 mm; total component volume 136400.607 mm³. The five components are separate solids, not a fused manufacturing part; volume is the sum of component volumes, including overlaps. An alternate `WING_SPAN=200` rebuild reimported as five valid solids with 207.2 mm overall X extent, confirming span changes propagate to the tip and the nacelle location. The delivered STEP is the default 180 mm rebuild. This is a visual approximation, not an engineering drawing or printability validation.
