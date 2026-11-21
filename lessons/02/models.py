"""Lesson 2: trace a synthetic contour image and build a spline keychain."""
from math import cos, pi, sin, isclose
from pathlib import Path

import cadquery as cq
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
CENTER = 210
PIXELS_PER_MM = 5
COLORS = ("#94b7ca", "#539297", "#275a68")
ANGLES = [2 * pi * index / 48 for index in range(48)]


def make_reference():
    image = Image.new("RGB", (421, 421), "#f3f7fa")
    draw = ImageDraw.Draw(image)
    for radius, color in zip((34, 25, 15), COLORS):
        pixels = []
        for angle in ANGLES:
            distance = PIXELS_PER_MM * radius * (1 + 0.12 * cos(3 * angle) + 0.08 * sin(2 * angle))
            pixels.append((CENTER + distance * cos(angle), CENTER - distance * sin(angle)))
        draw.polygon(pixels, fill=color)
    image.save(HERE / "contour-reference.png")
    return image


def trace(image, color):
    target = bytes.fromhex(color[1:])
    contour = []
    for angle in ANGLES[::2]:
        for distance in range(CENTER - 1, 0, -1):
            x = round(CENTER + distance * cos(angle))
            y = round(CENTER - distance * sin(angle))
            if image.getpixel((x, y)) == tuple(target):
                contour.append(((x - CENTER) / PIXELS_PER_MM, (CENTER - y) / PIXELS_PER_MM))
                break
        else:
            raise ValueError(f"No matching contour along angle {angle}")
    return contour


def terrain():
    image = make_reference()
    part = cq.Workplane("XY")
    for level, color in enumerate(COLORS):
        part = part.union(
            cq.Workplane("XY", origin=(0, 0, level * 3))
            .spline(trace(image, color), periodic=True).close().extrude(3)
        )
    # Mill an irregular summit basin plus shallow channels on the middle ledge.
    basin = (cq.Workplane("XY", origin=(0, 0, 6.8))
             .spline([(-9, 0), (-4, 6), (4, 5), (8, 0), (2, -4), (-5, -4)],
                     periodic=True).close().extrude(3))
    channels = (cq.Workplane("XY", origin=(0, 0, 4.9))
                .pushPoints([(-5, -20), (0, -20), (5, -20)]).slot2D(5, 1.4, 90).extrude(2))
    return part.cut(basin).cut(channels)


def keychain():
    outline = [(-25, 0), (-13, 12), (3, 15), (22, 8), (27, 0),
               (20, -9), (2, -14), (-13, -10)]
    body = (
        cq.Workplane("XY").spline(outline, periodic=True).close().extrude(4)
        .faces(">Z").workplane(centerOption="ProjectedOrigin").center(19, 0).hole(5)
    )

    pocket = (cq.Workplane("XY", origin=(-6, 0, 2.7))
              .ellipse(11, 7).extrude(2))
    grip = (cq.Workplane("XY", origin=(0, 0, 3.2))
            .pushPoints([(5, -7), (8, -5), (11, -3)]).slot2D(5, 1.3, 90).extrude(1.5))
    return body.cut(pocket).cut(grip)


if __name__ == "__main__":
    for name, part, height in (("terrain", terrain(), 9), ("keychain", keychain(), 4)):
        path = HERE / f"{name}.step"
        cq.exporters.export(part, str(path))
        result = cq.importers.importStep(str(path))
        assert len(result.solids().vals()) == 1 and result.val().isValid()
        assert isclose(result.val().BoundingBox().zlen, height, abs_tol=1e-5)
        if name == "keychain":
            bore = result.faces("%CYLINDER").val()
            assert isclose(bore._geomAdaptor().Cylinder().Radius(), 2.5, abs_tol=1e-5)
            assert len(result.section(2).val().Wires()) == 2
        else:
            areas = [result.section(z).val().Area() for z in (1, 4, 7)]
            assert areas[0] > areas[1] > areas[2] > 0
        x, y, z = (0, 0, 8) if name == "terrain" else (-6, 0, 3.5)
        assert not result.val().isInside(cq.Vector(x, y, z))
        assert result.val().isInside(cq.Vector(x, y, z - 1.5))
        print(f"{name}: valid single solid, {height} mm tall; feature checks passed")
