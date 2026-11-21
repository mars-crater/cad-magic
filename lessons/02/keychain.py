"""Whale-watching emblem: hand-traced in the reference image's 30-unit frame."""
from pathlib import Path

import cadquery as cq
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
BASE_HEIGHT = 3.2
RELIEF = 1.1
SCALE = 1.2
RING_X, RING_Y = 19, 12


def xy(u, v):
    """Place the reference on the left of the tag, with the flukes pointing up."""
    return (u - 15) * SCALE - 4, (15 - v) * SCALE


def curve(wire, points):
    return wire.spline([xy(u, v) for u, v in points], includeCurrent=True)


def flukes():
    # Use separate edges at the tips and notch; a periodic smooth fit rounds them off.
    wire = cq.Workplane("XY").moveTo(*xy(17.8, 24.5))
    wire = curve(wire, [(18.6, 24.4), (20.4, 24.8), (22.2, 25.2), (24, 24.8), (25.2, 24.4)])
    wire = curve(wire, [(24.2, 20), (21.4, 15), (17.1, 10.5), (16.5, 9.5), (16.6, 8.6)])
    wire = wire.lineTo(*xy(18.4, 2.7))
    wire = curve(wire, [(18.6, 1.3), (18.3, 0.3), (17.7, 0.1), (17.1, 0.3)])
    wire = wire.lineTo(*xy(12.3, 5.8))
    wire = curve(wire, [(11.8, 6.7), (11.8, 7.5), (12.1, 8.1)])
    wire = curve(wire, [(10.4, 7.8), (8.6, 8.0), (7.4, 8.4)])
    wire = wire.lineTo(*xy(3.4, 10.4))
    wire = curve(wire, [(3.0, 10.8), (3.0, 11.4), (5.5, 12.3), (10.4, 12)])
    wire = curve(wire, [(13.4, 12.6), (15.7, 15.0), (17.3, 19.6), (17.8, 24.5)])
    return wire.close().extrude(RELIEF)


def water():
    # The narrow strip of daylight between the water and tail matters more
    # to recognition than decorative surface marks.
    xs = [0.5 + i * 29 / 8 for i in range(9)]
    upper = [(x, 27.3 if i % 2 == 0 else 26.5) for i, x in enumerate(xs)]
    lower = [(x, v + 2.7) for x, v in upper]
    wire = cq.Workplane("XY").moveTo(*xy(*upper[0]))
    wire = curve(wire, upper[1:]).lineTo(*xy(*lower[-1]))
    return curve(wire, list(reversed(lower[:-1]))).close().extrude(RELIEF)


def build():
    base = (cq.Workplane("XY").rect(53, 43).extrude(BASE_HEIGHT)
            .edges("|Z").fillet(6).faces(">Z").edges().fillet(0.45))
    bore = cq.Workplane("XY").center(RING_X, RING_Y).circle(2.5).extrude(BASE_HEIGHT)
    relief = flukes().union(water()).translate((0, 0, BASE_HEIGHT))
    return base.cut(bore).union(relief)


def verify(reimported):
    """Check mounting geometry, separate relief islands, and reference silhouette."""
    shape = reimported.val()
    assert shape.isValid() and len(shape.Solids()) == 1
    assert abs(shape.BoundingBox().zlen - BASE_HEIGHT - RELIEF) < 1e-5
    bore_faces = [face for face in reimported.faces("%CYLINDER").vals()
                  if abs(face.Center().x - RING_X) < 1e-5
                  and abs(face.Center().y - RING_Y) < 1e-5]
    assert len(bore_faces) == 1
    bore = bore_faces[0]
    assert abs(bore._geomAdaptor().Cylinder().Radius() - 2.5) < 1e-5
    assert abs(bore.BoundingBox().zlen - BASE_HEIGHT) < 1e-5
    for z in (0.1, BASE_HEIGHT / 2, BASE_HEIGHT - 0.1):
        assert not shape.isInside(cq.Vector(RING_X, RING_Y, z))
        assert shape.isInside(cq.Vector(RING_X + 3, RING_Y, z))
    top = reimported.faces(">Z").vals()
    assert len(top) == 2, "Tail and water must stay visibly separate"
    with Image.open(HERE / "keychain-reference.png") as ref:
        reference = ref.convert("RGBA").getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    silhouette = Image.new("L", reference.size)
    draw = ImageDraw.Draw(silhouette)
    for face in top:
        vertices, triangles = face.tessellate(0.01, 0.08)
        pixels = [(((p.x + 4) / SCALE + 15) * reference.width / 30,
                   (15 - p.y / SCALE) * reference.height / 30) for p in vertices]
        for triangle in triangles:
            draw.polygon([pixels[i] for i in triangle], fill=255)
    traced = np.asarray(silhouette) > 0
    original = np.asarray(reference) > 0
    overlap = (traced & original).sum() / (traced | original).sum()
    assert overlap > 0.92, f"Whale silhouette overlap too low: {overlap:.3f}"
    return f"Whale and wave: reference overlap {overlap:.1%}; 5 mm ring bore, 1.1 mm relief"


if __name__ == "__main__":
    path = HERE / "keychain.step"
    cq.exporters.export(build(), str(path))
    print(verify(cq.importers.importStep(str(path))))
