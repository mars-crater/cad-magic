"""Parametric tower crane study; dimensions in mm, estimated from the course view."""
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Design:
    mast_bays: int = 18
    bay_height: float = 16
    mast_width: float = 16
    jib_bays: int = 19
    jib_length: float = 290
    counterjib_length: float = 47


def rod(start, end, radius):
    origin = cq.Vector(*start)
    axis = cq.Vector(*end) - origin
    unit = axis.normalized()
    overlap = radius / 2
    return cq.Solid.makeCylinder(radius, axis.Length + 2 * overlap, origin - unit * overlap, unit)


def cylinder(radius, length, bottom):
    return cq.Solid.makeCylinder(radius, length, cq.Vector(0, 0, bottom))


def block(x, y, z, dx, dy, dz):
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(x, y, z))


def mast(design):
    half = design.mast_width / 2
    top = design.mast_bays * design.bay_height
    corners = [(half, half), (-half, half), (-half, -half), (half, -half)]
    legs = [rod((*point, 0), (*point, top), 1.15) for point in corners]
    bracing = []
    for level in range(design.mast_bays + 1):
        z = level * design.bay_height
        for i, point in enumerate(corners):
            neighbor = corners[(i + 1) % 4]
            bracing.append(rod((*point, z), (*neighbor, z), .66))
            if level < design.mast_bays:
                first, last = (point, neighbor) if level % 2 == 0 else (neighbor, point)
                bracing.append(rod((*first, z), (*last, z + design.bay_height), .62))
    return legs[0].fuse(*legs[1:], *bracing).clean()


def jib(x_start, x_end, z, bays, tip_factor):
    def station(i):
        fraction = i / bays
        x = x_start + (x_end - x_start) * fraction
        factor = 1 + (tip_factor - 1) * fraction
        return [(x, -4.7 * factor, z), (x, 4.7 * factor, z), (x, 0, z + 8.5 * factor)]

    frames = [station(i) for i in range(bays + 1)]
    chords = [rod(a, b, .65) for a, b in zip(frames[0], frames[-1])]
    bracing = []
    for i, frame in enumerate(frames):
        for j, point in enumerate(frame):
            next_j = (j + 1) % 3
            bracing.append(rod(point, frame[next_j], .46))
            if i < bays:
                diagonal = (point, frames[i + 1][next_j])
                if i % 2:
                    diagonal = (frame[next_j], frames[i + 1][j])
                bracing.append(rod(*diagonal, .44))
    return chords[0].fuse(*chords[1:], *bracing).clean()


def build(design=Design()):
    top = design.mast_bays * design.bay_height
    boom_z = top + 16
    apex = (0, 0, boom_z + 28)
    lower = mast(design).fuse(cylinder(14, 3, -2), cylinder(14, 3, top - 1)).clean()
    tower_top = [
        cylinder(9, 4.2, top + 2),
        block(-6, -6, top + 6, 12, 12, 11),
        block(-10, -8, top + 7, 14, 16, 8),
        block(-8, -8, boom_z - .3, 16, 16, 2.5),
        rod((0, -4.2, boom_z + 1), apex, .76),
        rod((0, 4.2, boom_z + 1), apex, .76),
        rod(apex, (-design.counterjib_length + 4, 0, boom_z + 8.1), .46),
        rod(apex, (design.jib_length * .24, 0, boom_z + 7.2), .46),
        block(-design.counterjib_length - 2, -5.8, boom_z - 9.3, 11, 11.6, 13),
    ]
    forward = jib(0, design.jib_length, boom_z, design.jib_bays, .25)
    backward = jib(0, -design.counterjib_length, boom_z, 4, .88)
    return lower.fuse(forward, backward, *tower_top).clean()


def verify(part, design):
    assert part.isValid() and len(part.Solids()) == 1
    top = design.mast_bays * design.bay_height
    bounds = part.BoundingBox()
    assert abs(bounds.zmin + 2) < 1e-5
    assert abs(bounds.xmin + design.counterjib_length + 2) < 1e-5
    assert design.jib_length < bounds.xmax < design.jib_length + 1.3
    assert top + 44 < bounds.zmax < top + 45.2
    assert not part.isInside((0, 0, design.bay_height / 2))
    assert part.isInside((design.mast_width / 2, design.mast_width / 2, design.bay_height / 2))
    assert part.isInside((0, 0, -1))
    print(f"valid; one solid; extents {bounds.xlen:.2f} × {bounds.ylen:.2f} × {bounds.zlen:.2f} mm")


if __name__ == "__main__":
    design = Design()
    part = build(design)
    verify(part, design)
    path = HERE / "crane.step"
    cq.exporters.export(part, str(path))
    reopened = cq.importers.importStep(str(path)).val()
    verify(reopened, design)
    assert abs(part.Volume() - reopened.Volume()) / part.Volume() < 1e-6
