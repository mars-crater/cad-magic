"""Loft a banana from paired landmarks on the course CAD side silhouette.

Coordinates are traced from Banana.png at 850 px width; the 170 mm class
overall length is a visual scale choice, not FIG-specified fruit geometry.
"""
from pathlib import Path

import cadquery as cq
from cadquery import Vector

HERE = Path(__file__).resolve().parent
MM_PER_PIXEL = .35

# Outer and inner shoulder landmarks from stem shoulder to blossom end.
BODY = [
    ((223, 197), (261, 188)),
    ((212, 231), (284, 213)),
    ((215, 268), (312, 242)),
    ((238, 312), (344, 274)),
    ((269, 354), (384, 303)),
    ((315, 396), (427, 323)),
    ((374, 432), (477, 338)),
    ((443, 459), (530, 346)),
    ((513, 472), (580, 350)),
    ((580, 467), (620, 353)),
    ((637, 451), (656, 359)),
    ((672, 427), (674, 364)),
    ((694, 398), (682, 367)),
]
STEM = [
    ((201, 105), (249, 90)),
    ((208, 139), (253, 126)),
    ((215, 172), (257, 160)),
    BODY[0],
]

# Five rounded flanks joined along deliberate longitudinal peel shoulders.
# The two profile extrema are exact; intermediate coordinates vary in depth.
CORNERS = [(1, .20), (.43, 1), (-1, .10), (-.55, -.86), (.53, -.91)]
FLANKS = [(.81, .66), (-.36, .76), (-.86, -.46), (-.02, -1.05), (.87, -.45)]


def section(outer, inner, depth_ratio):
    lower = Vector((outer[0] - 200) * MM_PER_PIXEL, 0, (473 - outer[1]) * MM_PER_PIXEL)
    upper = Vector((inner[0] - 200) * MM_PER_PIXEL, 0, (473 - inner[1]) * MM_PER_PIXEL)
    center = (lower + upper) * .5
    shoulder = (upper - lower) * .5
    depth = Vector(0, depth_ratio * shoulder.Length, 0)

    def at(coordinates):
        profile, transverse = coordinates
        return center + profile * shoulder + transverse * depth

    edges = [
        cq.Edge.makeSpline([at(corner), at(flank), at(CORNERS[(index + 1) % len(CORNERS)])])
        for index, (corner, flank) in enumerate(zip(CORNERS, FLANKS))
    ]
    return cq.Wire.assembleEdges(edges)


def build(depth_ratio=.69):
    stem = [section(*points, depth_ratio) for points in STEM]
    body = [stem[-1]] + [section(*points, depth_ratio) for points in BODY[1:]]
    blossom = section((697, 395), (685, 370), depth_ratio * .78)
    return cq.Solid.makeLoft(stem).fuse(
        cq.Solid.makeLoft(body), cq.Solid.makeLoft([body[-1], blossom], ruled=True)
    ).clean()


def check(part):
    assert part.isValid() and len(part.Solids()) == 1
    box = part.BoundingBox()
    assert 170 < box.xlen < 180 and 130 < box.zlen < 140 and 30 < box.ylen < 40
    return box


if __name__ == "__main__":
    banana = build()
    original = check(banana)
    thicker = build(.81)
    assert thicker.isValid() and len(thicker.Solids()) == 1
    changed = thicker.BoundingBox()
    assert changed.ylen - original.ylen > 5
    assert abs(changed.xlen - original.xlen) < .05 and abs(changed.zlen - original.zlen) < .05
    path = HERE / "banana.step"
    cq.exporters.export(banana, str(path))
    imported = cq.importers.importStep(str(path)).val()
    box = check(imported)
    assert abs(imported.Volume() - banana.Volume()) / banana.Volume() < 1e-5
    print(f"Reopened banana: one valid solid; bounds {box.xlen:.2f} × {box.ylen:.2f} × {box.zlen:.2f} mm")
    print(f"Depth edit: {original.ylen:.2f} → {changed.ylen:.2f} mm; x/z profile unchanged within 0.05 mm")
