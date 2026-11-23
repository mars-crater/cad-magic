# Fouled anchor · keychain

The defining detail is the continuous rope crossing the interrupted shank: a plain anchor would retain its flukes but lose the supplied emblem’s identity. Before building the full plaque, I cropped the central crossing at the final artwork scale (0.44 mm/SVG unit), built a 13 × 11 mm base coupon, exported and reopened coupon.step, and inspected its single-material top and oblique views. The diagonal remained continuous, with the shank stopping short on both sides. I retained that geometry for the complete plaque. This is a digital target-scale geometry test, not a physical-size print or viewer study.

## Evidence from saved geometry

- Coupon: one valid solid, 13 × 11 × 3.8 mm. At x=0, z=2.8 mm the two open intervals flanking the rope measured 1.335 and 1.332 mm along the shank. At z=3.55 only the rope remained (y=2.435 to 5.133 mm). Anchor and rope project 0.85 and 1.40 mm above the 2.40 mm backing.
- Final STEP reimport: one valid solid, 60.00 × 78.00 × 3.80 mm. A separate Ø4.8 mm cylindrical cut centered at (0,29.04) opens through the backing inside the artwork’s eye. Reimported center was empty and adjacent wall at x=2.45 mm solid at z=0.10, 1.20 and 2.39 mm. Nominal top ligament from bore to plate edge: 7.56 mm.
- Reimported XY section masks vs independently rasterized supplied SVG: intersection/union 0.9922 for all raised ink at z=2.8 and 0.9698 for rope alone at z=3.55. The final top view retains the eye, crossbar, swept arms, two flukes, winding rope and interruptions in the shank.
- Views show saved STEP geometry with one material, not the supplied colored SVG. Views fit independently to frame; the coupon is enlarged relative to the keychain. Top images span 84 mm (final) and 14.4 mm (coupon) vertically.

## Rebuild

From the assignment folder, use .venv/bin/python with submission/model.py coupon, then submission/render.py coupon; inspect the coupon before running submission/model.py final, submission/render.py final and submission/check.py. model.py and reference.svg together are the editable source. The STEP exports contain geometry, not construction history.

## Simplifications and limits

Color is translated to level and negative space, not painted. SVG curves become polygonal outlines traced at six samples per SVG unit with a 0.75-pixel simplification tolerance. The stepped eye has a smaller functional bore rather than opening the entire graphic eye. The blank is a rounded rectangle and back is flat. Section agreement measures silhouette at two heights, not machining tolerances. No print, ring fit, wear or pull test was performed.
