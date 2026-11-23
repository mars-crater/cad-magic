"""Editable unstrung squash racquet study; dimensions in mm, not course dimensions."""
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Design:
    head_base: float = 284
    head_length: float = 396
    head_half_width: float = 104
    rim_half_width: float = 4.4
    rim_half_depth: float = 6
    hole_count: int = 42
    hole_radius: float = 1.25


def head_centerline(design, offset=0, z=0):
    # Two Bézier spans per side. The offset sections
    # share the same axis and knots to align the ruled transitions.
    width = design.head_half_width + offset
    bottom = design.head_base - offset
    height = design.head_length + 2 * offset
    lower = [(0, 0), (.18, 0), (.99, .33), (1, .64)]
    upper = [(1, .64), (1.01, .87), (.60, 1), (0, 1)]
    profiles = [lower, upper,
                [(-x, y) for x, y in reversed(upper)],
                [(-x, y) for x, y in reversed(lower)]]
    edges = [cq.Edge.makeBezier([cq.Vector(x * width, bottom + y * height, z)
                                 for x, y in control_points])
             for control_points in profiles]
    return cq.Wire.assembleEdges(edges)


def head(design):
    depth = design.rim_half_depth
    width = design.rim_half_width
    bevel = 1.3

    def loft(sign, half_depth):
        sections = [(-half_depth, width - bevel), (-depth + bevel, width),
                    (depth - bevel, width), (half_depth, width - bevel)]
        wires = [head_centerline(design, sign * offset, z)
                 for z, offset in sections]
        return cq.Solid.makeLoft(wires, ruled=True)

    return loft(1, depth).cut(loft(-1, depth + .1)).clean()


def handle():
    # Sections are transverse to the centerline. The rounded elliptical section
    # flares at the butt, narrows toward the shaft, and widens again at the throat.
    sections = [
        (0, 17, 12), (4, 19, 13), (11, 18, 12.7), (152, 16.5, 11),
        (158, 16, 10), (166, 9.1, 7.6), (225, 8.2, 6.7),
        (260, 8.4, 6.1), (278, 10.5, 6.4), (286, 9, 5.5),
    ]

    def wire(y, width, depth):
        plane = cq.Plane(origin=(0, y, 0), xDir=(1, 0, 0), normal=(0, 1, 0))
        return cq.Workplane(plane).ellipse(width, depth).val()

    grip = cq.Solid.makeLoft([wire(*section) for section in sections[:5]], ruled=True)
    stem = cq.Solid.makeLoft([wire(*section) for section in sections[4:]], ruled=True)
    return grip.fuse(stem).clean()


def grommet_axes(path, design):
    # Exclude the reinforced throat junction. Follow the local frame without
    # projecting holes to a fixed center, which would skew the side openings.
    for index in range(1, design.hole_count + 1):
        fraction = .032 + index / (design.hole_count + 1) * .936
        point = path.positionAt(fraction)
        tangent = path.tangentAt(fraction)
        yield point, cq.Vector(tangent.y, -tangent.x, 0)


def build(design=Design()):
    path = head_centerline(design)
    cutters = []
    reach = 2 * design.rim_half_width + 3
    for point, normal in grommet_axes(path, design):
        cutters.append(cq.Solid.makeCylinder(design.hole_radius, 2 * reach, point - reach * normal, normal))
    return head(design).fuse(handle()).cut(*cutters).clean()


def verify(part, design):
    assert part.isValid() and len(part.Solids()) == 1
    bounds = part.BoundingBox()
    assert abs(bounds.ymin) < 1e-5
    assert abs(bounds.ymax - (design.head_base + design.head_length + design.rim_half_width)) < .03
    assert not part.isInside((0, design.head_base + design.head_length / 2, 0))
    assert part.isInside((0, 80, 0))
    for point, normal in grommet_axes(head_centerline(design), design):
        # Probe the whole open bore, then confirm material remains above it.
        reach = 2 * design.rim_half_width + 3
        for index in range(-8, 9):
            offset = index * reach / 8
            assert not part.isInside(point + offset * normal)
        assert part.isInside(point + cq.Vector(0, 0, 3))
    print(f"valid; one solid; {design.hole_count} grommet paths open; "
          f"extents {bounds.xlen:.2f} × {bounds.ylen:.2f} × {bounds.zlen:.2f} mm")


if __name__ == "__main__":
    design = Design()
    part = build(design)
    verify(part, design)
    path = HERE / "squash-racquet.step"
    cq.exporters.export(part, str(path))
    reopened = cq.importers.importStep(str(path)).val()
    verify(reopened, design)
    assert abs(part.Volume() - reopened.Volume()) / part.Volume() < 1e-5
