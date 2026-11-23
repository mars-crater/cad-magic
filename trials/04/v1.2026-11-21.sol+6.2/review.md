# Independent review — vacuum adaptor

Baseline: [dimensioned brief](brief.md), [protocol](protocol.md), [pinned skill](revision.txt). This is an original written design, not an image-matching exercise.

| Criterion | Verdict | Evidence |
|---|---|---|
| Length, inlet, offset ellipse | Pass | Reopened the [STEP](results/vacuum-adaptor.step) in CadQuery; independently intersected it with planes normal to X. At X=0, outer/bore Y×Z extents were 40×40/36×36 mm, centered at Z=0; at X=40 they were 42×22/38×18, centered at Z=8. Reran the submission’s sampled circle/ellipse residual assertions. |
| Mouth size, radius and orientation | Pass | X=80 plane yielded 54×14/50×10, centered at Z=0, long axis Y. Rerunning the exported-skin profile check gave maximum deviation 0.000001 mm from the R3 outer contour. End-to-end X extent also passed the 0.001 mm assertion. |
| Nominal wall | Pass | Independent sections every 10 mm gave about 4 mm difference in both overall spans (2 mm each side). Reran the builder’s denser 17-section sample: minimum in-plane wall per section ranged 1.991–2.000 mm. Not a full 3D normal-thickness map. |
| Continuous passage, single solid, no fittings | Pass | Reimport yielded one valid solid, volume 16715.23 mm³, two B-spline skins and two planar annular end faces. Each of nine cuts from X=0 through 80 produced two nested wires; bore heights ranged from 36 to 10 mm. No intervening wall or attached fitting. The submission’s seam tangent and centerline void checks also passed. |
| Editable source | Pass | Ran [verification](scripts/verify.py) including rebuilding with the inlet changed from 40 to 44 mm: bore became 40 mm and other specified stations retained their dimensions. |
| Three-quarter render and visual fidelity | Pass | Inspected the [render](renders/vacuum-adaptor.png): the upward sweep and broad low mouth read clearly, with an exposed rim and interior. The far inlet is edge-on; circularity and the exact intermediate profile are established by sections, not by this view. |
| Finish | N/A | No finish requested. |

No blocking failure or meaningful departure from the written brief was found. This establishes CAD geometry, not measured airflow, physical fit or manufacturing performance.
