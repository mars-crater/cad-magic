# 04 · Lofts and sweeps

MIT IAP 2024 · Andy Eskenazi · Session 4. The session slides introduce SolidWorks loft and sweep; the editable studies here use CadQuery.

## What I learned

Choose the operation by what controls the shape: sweep a profile along a path when its cross-section stays the same; loft when the design specifies different sections at different stations. Match profile landmarks from one station to the next, then check cuts through the export. A side silhouette cannot establish whether a cavity stays open. See the [CAD Magic workflow](../../skills/cad-magic/SKILL.md).

## Course exercises

The slide deck introduces the boat hull, airport control tower and banana. The repository also contains crane and squash racquet studies. These are interpretations, not dimensioned replicas.

## Practice results

The [hull](hull/boat-hull.png) joins a sequence of waterlines, then subtracts an inner loft. Its [cutaway](hull/boat-hull-section.png) exposes the cavity. The [tower](tower/sydney-control-tower.png) aligns polygon corners to preserve the cab facets; the [banana](banana/banana.png) uses paired silhouette landmarks and a separate depth parameter.

## Verification and limits

In the [independent adaptor trial](../../trials/04/v1.2026-11-21.sol+6.2/review.md), the reopened STEP had a circular inlet, an offset elliptical middle and a rounded rectangular mouth. Seventeen sampled sections gave minimum in-plane wall values of 1.991–2.000 mm. This is not a constant-normal-thickness test; the course hull's paired lofts make no such guarantee either. The adaptor passed with the **pre-update** skill: it validates the method on another subject, not an improvement caused by this edit. No separate sweep trial or physical test is claimed. The [trial ledger](../../trials/04/README.md) records which findings were adopted.

The [banana reproduction review](../../trials/04/v2.2026-11-21.sol+6.2/results/review.md) found that changing estimated depth preserved the projected dimensions but identified overstated ridges and an angular tip. Keeping unseen depth independently editable remains a candidate for transfer testing, not a finding about the fruit’s actual depth.

## Artifacts and rebuild

With the repository requirements installed, run `python lessons/04/hull/model.py` from the repository root to rebuild the hull and run its checks. The other model scripts can be run the same way.

| Study | Parametric source | STEP export |
|---|---|---|
| Hull | [model](hull/model.py) | [STEP](hull/boat-hull.step) |
| Control tower | [model](tower/model.py) | [STEP](tower/sydney-control-tower.step) |
| Banana | [model](banana/model.py) | [STEP](banana/banana.step) |
| Crane | [model](crane/model.py) | [STEP](crane/crane.step) |
| Squash racquet | [model](racquet/model.py) | [STEP](racquet/squash-racquet.step) |

## Sources

[MIT OpenCourseWare course](https://ocw.mit.edu/courses/res-16-002-how-to-cad-almost-anything-january-iap-2024/) · [Instructor’s Session 4 materials and slides](https://github.com/andyeske/How-to-CAD-Almost-Anything/tree/main/Session%20Files/Session%204). Original course materials remain under their respective terms.
