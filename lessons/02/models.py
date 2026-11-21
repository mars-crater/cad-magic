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
    return part


def keychain():
    outline = [(-25, 0), (-13, 12), (3, 15), (22, 8), (27, 0),
               (20, -9), (2, -14), (-13, -10)]
    return (
        cq.Workplane("XY").spline(outline, periodic=True).close().extrude(4)
        .faces(">Z").workplane(centerOption="ProjectedOrigin").center(19, 0).hole(5)
    )


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
        print(f"{name}: valid single solid, {height} mm tall; feature checks passed")
