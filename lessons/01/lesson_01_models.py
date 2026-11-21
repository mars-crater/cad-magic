"""Rebuild and verify the Lesson 1 models with CadQuery; dimensions are mm."""
from math import isclose
from pathlib import Path

import cadquery as cq

INCH = 25.4
HERE = Path(__file__).resolve().parent


def cake(second_diameter=72):
    diameters = (94, second_diameter, 50, 30)
    cake_solid = cq.Workplane("XY").circle(diameters[0] / 2).extrude(12)
    for diameter in diameters[1:]:
        cake_solid = cake_solid.faces(">Z").workplane().circle(diameter / 2).extrude(12)
    for level, diameter in enumerate(diameters):
        # Cut two narrow frosting channels around each tier.
        for height in (3, 8):
            groove = (cq.Workplane("XY", origin=(0, 0, level * 12 + height))
                      .circle(diameter / 2 + 0.5).circle(diameter / 2 - 1).extrude(1.4))
            cake_solid = cake_solid.cut(groove)
    return cake_solid.faces(">Z").edges().chamfer(1).faces(">Z").workplane().hole(6, 4)


def phone():
    width, length, depth = (size * INCH for size in (2.64, 5.44, 0.27))
    body = (
        cq.Workplane("XY").rect(width, length).extrude(depth)
        .edges("|Z").fillet(8)
        .faces(">Z").edges().fillet(0.7)
        .faces(">Z").workplane().center(0, -length / 2 + 7).hole(10, 0.6)
    )

    screen = (cq.Workplane("XY", origin=(0, 0, depth - 0.9))
              .rect(width - 8, length - 28).extrude(1.5).edges("|Z").fillet(3))
    speaker = (cq.Workplane("XY", origin=(0, length / 2 - 7, depth - 1.2))
               .slot2D(14, 2.6).extrude(2))
    return body.cut(screen).cut(speaker)


def pencil():
    tip, shaft, ferrule, eraser = (size * INCH for size in (0.53, 5, 0.45, 0.15))
    radius = 0.14 * INCH
    # Use the specified circumscribed radius; the flats round to .24 in,
    # slightly below the .25 in dimension shown in section A–A.
    barrel = cq.Workplane("XY", origin=(0, 0, tip)).polygon(6, 2 * radius).extrude(shaft)
    point = cq.Solid.makeCone(0, radius, tip)
    # Clip the cone to the hexagonal silhouette where it meets the barrel.
    point = cq.Workplane("XY").newObject([point]).intersect(
        cq.Workplane("XY").polygon(6, 2 * radius).extrude(tip)
    )
    tail = (
        cq.Workplane("XY", origin=(0, 0, tip + shaft)).circle(radius)
        .extrude(ferrule + eraser).faces(">Z").edges().fillet(0.02 * INCH)
    )
    for offset in (1.4, 3.1, 5, 7, 9, 11.4):
        groove = (cq.Workplane("XY", origin=(0, 0, tip + shaft + offset))
                  .circle(radius + 0.3).circle(radius - 0.42).extrude(0.7))
        tail = tail.cut(groove)
    return barrel.union(point).union(tail)


def check(part, expected):
    solid = part.val()
    box = solid.BoundingBox()
    assert solid.isValid() and len(part.solids().vals()) == 1
    measured = (box.xlen, box.ylen, box.zlen)
    assert all(isclose(actual, target, abs_tol=1e-4) for actual, target in zip(measured, expected))
    return measured


if __name__ == "__main__":
    resized = cake(68)
    check(resized, (94, 94, 48))
    second_tier = cq.Workplane("XY").newObject([resized.val()]).section(18).val().BoundingBox()
    assert isclose(second_tier.xlen, 68, abs_tol=1e-4)
    assert isclose(second_tier.center.x, 0, abs_tol=1e-4)
    assert isclose(second_tier.center.y, 0, abs_tol=1e-4)
    print("Resized second cake tier: 68 mm, centered on X/Y")

    for name, model, expected in (
        ("cake", cake(), (94, 94, 48)),
        ("phone", phone(), tuple(value * INCH for value in (2.64, 5.44, 0.27))),
        ("pencil", pencil(), (0.28 * INCH, 0.28 * INCH, 6.13 * INCH)),
    ):
        measured = check(model, expected)
        path = HERE / f"lesson-01-{name}.step"
        cq.exporters.export(model, str(path))
        rebuilt = cq.importers.importStep(str(path))
        check(rebuilt, expected)
        # Probe the recess and neighboring retained material on the STEP solid.
        void, material = {
            "cake": ((46.6, 0, 3.5), (46.6, 0, 5)),
            "phone": ((0, 0, 6.3), (0, 0, 5.7)),
            "pencil": ((3.4, 0, 142.2), (3.4, 0, 143)),
        }[name]
        assert not rebuilt.val().isInside(cq.Vector(*void))
        assert rebuilt.val().isInside(cq.Vector(*material))
        print(f"{name}: {tuple(round(value, 3) for value in measured)} mm; STEP round-trip valid")
