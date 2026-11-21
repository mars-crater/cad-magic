# Maintaining CAD Magic

CAD Magic is a skill first. The [skill](skills/cad-magic/SKILL.md) tells an agent how to do the work; the [lesson index](lessons/README.md) points to evidence that the techniques work. Keep the [root README](README.md) focused on agent capabilities. Put exercises, original course credits, build commands, artifacts, and observed results on the lesson pages.

## Keep each change coherent

- **Geometry or quality change:** Edit the parametric source, rebuild the affected exports, then reimport and check them. Regenerate renders from those exports, not from a reference image or an earlier revision. Inspect the new views at normal reading size and add a close-up or section if the changed detail is hard to see.
- **Render change:** Reuse one canonical image per view. Check every affected embed, link, caption, and alt text, including the lesson page and lesson index. Search the repo for the old asset name before renaming or replacing it. Where pages share the same image path, update the asset once rather than making duplicate copies.
- **Technique change:** Decide whether the improvement generalizes. If it does, add the reusable decision rule and its verification method to the skill, and link the lesson evidence. Update the index with what the lesson demonstrated; update the root README only if the public capability changed. Keep one-off dimensions and exercise instructions out of the skill.
- **Documentation change:** Follow the established lesson headings and preserve attribution and license boundaries. Link third-party course material rather than treating it as project-owned. Keep expected, observed, and untested results distinct.

## Check quality against the requested work

- **Size or scale:** Identify units and critical dimensions, fits, or clearances. Verify those on the rebuilt export. For editable geometry, change a driving dimension and check what should stay fixed. Evaluate fine details at the intended output scale, not just in a zoomed render.
- **Texture or finish:** Ask of the result whether the texture must exist in the solid or only in the render. For modeled relief, check representative depth, width, or spacing and inspect under angled light. Do not claim appearance-only treatment survives a geometry export.
- **Trim, fillet, or chamfer:** Check that the intended boundary changed and neighboring faces or critical dimensions were preserved. Use a section or close-up when the trim is small or hidden.
- **Hole, pocket, or crevice:** Check position and size where relevant. Use a section or solid probes to distinguish a through-hole from a blind cut and confirm material remains where intended. An attractive shadow is not proof of a cut.
- **Print work:** When printability is part of the task, check the intended scale in a slicer and distinguish that from a physical print test.

Before finishing, review the affected source, export, render, and documentation together. Run the relevant rebuild and feature checks, resolve changed links, and verify actual results against the request. For a documentation-only edit, check links and consistency without churning unchanged CAD assets. Report what was checked and any limitations.
