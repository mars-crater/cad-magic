# CAD Magic

**Work in progress.** [CAD Magic is an agent skill](skills/cad-magic/SKILL.md) for turning dimensions, sketches, or reference images into editable CAD models with checks that show what works.

## What the skill gives an agent

- **Model for change.** Choose stable references and encode design intent so dimensions can change without losing alignment. Build the main volumes before cuts and edge details.
- **Turn a reference into geometry.** Identify the features that make the subject recognizable, trace at a known scale, then compare the exported geometry against the source. Keep functional dimensions such as hole sizes independent of the trace.
- **Hand off checked results.** Provide editable source, reimport exported STEP files to check geometry, and render the saved model when a visual preview is needed. Report what was measured, estimated, and not tested.

## Use the skill

Point your agent at [`skills/cad-magic/SKILL.md`](skills/cad-magic/SKILL.md) and describe the part, its critical dimensions, and the outputs you need. The workflow works with the project's existing CAD tool; the examples use CadQuery.

The [lesson index](lessons/README.md) records what each exercise demonstrated and links to the models, renders, and rebuild instructions. Lessons are evidence for the skill, not prerequisites for using it.

## Credit

Based on [How to CAD Almost Anything (RES.16-002, MIT IAP 2024)](https://ocw.mit.edu/courses/res-16-002-how-to-cad-almost-anything-january-iap-2024/), taught by **Andy Eskenazi** and made available by **MIT OpenCourseWare**. See the [instructor's original workshop repository](https://github.com/andyeske/How-to-CAD-Almost-Anything) for the slides, recordings, and original SolidWorks files. This is not an official MIT course repository and does not redistribute the original materials.

## License

Original CAD Magic code, skill instructions, notes, models, and renders are
available under the [MIT License](LICENSE). Lesson 2’s [elevation data](lessons/02/terrain-source.md) and [pictogram artwork](lessons/02/keychain-reference-LICENSE.txt) retain their source terms. Linked MIT OpenCourseWare materials
and instructor resources remain under their respective terms; this license does
not apply to them.
