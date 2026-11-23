"""Sydney control tower interpreted from the Session 4 course screenshot."""
from math import cos, pi, sin
from pathlib import Path

import cadquery as cq
from cadquery import Vector

HERE = Path(__file__).resolve().parent
LOBE_Z = 146
CAB_Z = 166
CAB_TOP = 187


def cylinder(radius, height, z, x=0, y=0):
    return cq.Solid.makeCylinder(radius, height, Vector(x, y, z))


def rod(start, end, radius):
    first, last = Vector(*start), Vector(*end)
    axis = last - first
    return cq.Solid.makeCylinder(radius, axis.Length, first, axis.normalized())


def polygon_ring(radius, elevation, sides=20, x=0, y=0, phase=0):
    points = [
        Vector(x + radius * cos(2 * pi * i / sides + phase),
               y + radius * sin(2 * pi * i / sides + phase), elevation)
        for i in range(sides)
    ]
    return cq.Wire.makePolygon(points, close=True)


def cabin(upper_radius):
    # Aligned polygon corners loft into the visibly faceted, upward-flaring cab.
    levels = [(19, CAB_Z - .4), (21, CAB_Z + 4), (upper_radius - 3.5, CAB_TOP - 6), (upper_radius, CAB_TOP)]
    glazing = cq.Solid.makeLoft([polygon_ring(radius, z) for radius, z in levels], ruled=True)
    belt = cq.Solid.makeLoft(
        [polygon_ring(upper_radius - 2.75, CAB_TOP - 6.1), polygon_ring(upper_radius - 2.15, CAB_TOP - 5.1)],
        ruled=True,
    )
    return [glazing, belt, cylinder(upper_radius + .5, 1.1, CAB_TOP - .25)]


def ribbon():
    # A single smooth loft through rotated rectangular radial sections.
    # Unlike an extrusion, radial stand-off can change along the rising turn.
    sections = []
    for i in range(33):
        fraction = i / 32
        angle = pi * (1 - 2.05 * fraction)
        radius = 38 - 22 * fraction + 4 * sin(pi * fraction)
        z = 22 + 124.5 * fraction
        points = [
            Vector((radius + dr) * cos(angle), (radius + dr) * sin(angle), z + dz)
            for dr, dz in [(-.75, -8), (.75, -8), (.75, 8), (-.75, 8)]
        ]
        sections.append(cq.Wire.makePolygon(points, close=True))
    return cq.Solid.makeLoft(sections)


def build(upper_radius=28):
    parts = [
        cylinder(75, 3, 0),
        cylinder(54, 12, 2.5),
        cylinder(54.25, 2, 13.5),
        cq.Solid.extrudeLinear(polygon_ring(8, 15, 4, phase=pi / 8), [], Vector(0, 0, 134)),
        cylinder(30, 20.5, LOBE_Z),
        cylinder(4.5, 7, CAB_TOP + .5),
        cylinder(10, 8, 15, -23, -17),
        rod((-38, 0, 14), (-38, 0, 26), 3),
    ]
    parts.append(cq.Solid.makeBox(19, 2, 1.8, Vector(-9.5, -1, 194)))
    for row in range(1, 15):
        shaft_band = polygon_ring(8.45, 15 + 8.8 * row, 4, phase=pi / 8)
        parts.append(cq.Solid.extrudeLinear(shaft_band, [], Vector(0, 0, .85)))
    for i in range(5):
        theta = 2 * pi * i / 5 - pi / 2
        x, y = 30 * cos(theta), 30 * sin(theta)
        parts.extend([
            cq.Solid.extrudeLinear(polygon_ring(17, LOBE_Z, 24, x, y), [], Vector(0, 0, 18)),
            cq.Solid.extrudeLinear(polygon_ring(17.28, LOBE_Z + 6, 24, x, y), [], Vector(0, 0, .7)),
            cq.Solid.extrudeLinear(polygon_ring(17.28, LOBE_Z + 12, 24, x, y), [], Vector(0, 0, .7)),
            cylinder(17.35, 2.2, LOBE_Z + 17.9, x, y),
        ])
        antenna_radius = upper_radius - 3
        a, b = antenna_radius * cos(theta), antenna_radius * sin(theta)
        parts.append(cq.Solid.makeCone(.65, .24, 24 + i % 3 * 2, Vector(a, b, CAB_TOP + .65)))
    for angle in (pi * .20, pi * .86, pi * 1.65):
        dx, dy = cos(angle), sin(angle)
        parts.extend([
            rod((59 * dx, 59 * dy, 4), (10 * dx, 10 * dy, LOBE_Z + 2), .85),
            cq.Solid.makeCone(5, 2, 12, Vector(57 * dx, 57 * dy, 2.8)),
        ])
    parts.extend(cabin(upper_radius))
    parts.append(ribbon())
    return parts[0].fuse(*parts[1:]).clean()


def check(part):
    assert part.isValid() and len(part.Solids()) == 1
    box = part.BoundingBox()
    assert abs(box.xlen - 150) < .001 and abs(box.ylen - 150) < .001
    assert abs(box.zlen - 215.65) < .001
    return box


if __name__ == "__main__":
    tower = build()
    original = check(tower)
    wider = build(31)
    changed = check(wider)
    assert abs(original.zlen - changed.zlen) < .001
    assert not tower.isInside(Vector(29.5, 0, CAB_TOP + .25))
    assert wider.isInside(Vector(29.5, 0, CAB_TOP + .25))
    path = HERE / "sydney-control-tower.step"
    cq.exporters.export(tower, str(path))
    imported = cq.importers.importStep(str(path)).val()
    box = check(imported)
    assert abs(imported.Volume() - tower.Volume()) / tower.Volume() < 1e-5
    print(f"Reopened tower: one valid solid; bounds {box.xlen:.2f} × {box.ylen:.2f} × {box.zlen:.2f} mm")
    print("Cab radius edit: 28 → 31 mm; roof expands while footprint and height remain fixed")
