---
name: cad-magic
description: Build, revise, verify, or render simple parametric CAD parts using workflows practiced in MIT's How to CAD Almost Anything. Use for CAD Magic exercises and sketch-based mechanical models, not generic image generation.
---

# CAD Magic

1. Identify the deliverable, units, and dimensions that matter. Separate measured or specified dimensions from visual estimates. If a drawing disagrees with itself, record which dimension governs rather than silently rounding away the discrepancy.
2. Choose a sketch plane and stable origin. Express design intent through dimensions and relations in sketch-based CAD, or through shared parameters and explicit references in code-based CAD. Reuse the existing model's toolchain; for new headless exercises, CadQuery is a demonstrated option.
3. Build the main volumes before details: extrude profiles, cut recesses, then add edge treatments where appropriate. Keep editable source separate from STEP exports. Don't describe a code-based profile as solver-verified or a STEP file as an editable feature history.
4. Verify the expected solid count, geometric validity, and critical dimensions. Change a meaningful parameter and rebuild to test an intended invariant, such as concentricity. If exporting STEP, reimport and repeat the geometry checks.
5. When asked to show the result, render the actual saved geometry and inspect the image before sharing. Label independent display scales. For print work, check the intended scale in the slicer; CAD validity alone is not proof of printability.
6. Report artifacts, assumptions, checks run, and limits. For course work, distinguish what was read or watched from what was built and verified.

## Current lesson reference

Start with [Lesson 1 notes](../../lessons/01/README.md) and the [CadQuery examples](../../lessons/01/lesson_01_models.py): the cake tests design intent under resize; the phone works from a picture plus an overall envelope; the pencil works from an engineering drawing. Add later techniques after practicing them, keeping lesson-specific records in the lessons directory.
