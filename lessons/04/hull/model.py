"""Loft a hull from waterlines and cut the opening to a rising sheer."""
import argparse
import math
from pathlib import Path

import cadquery as cq
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections

HERE = Path(__file__).resolve().parent

# Waterline envelopes estimated from the course drawing. X increases from
# stern to bow. Widths are half-breadths; Z is measured from the loft's base.
# (height, aft limit, forward limit, maximum half-breadth, transom fullness)
WATERLINES = (
    (0, 78, 243, 5, 0.12),
    (2, 74, 248, 10, 0.12),
    (4.8, 66, 261, 16.5, 0.12),
    (8.5, 57, 274, 23, 0.13),
    (17, 46, 285, 33.5, 0.15),
    (26, 34, 294, 42, 0.19),
    (35, 19, 300, 47.5, 0.27),
    (43, 7, 305, 51, 0.41),
    (51, 3, 309, 52.5, 0.66),
    (59, 1.4, 313, 53.3, 0.85),
    (68, 0, 317, 53.5, 0.88),
    (81, -1.6, 323, 53.5, 0.89),
)
SHEER = ((-6, 64), (22, 62.7), (80, 61), (132, 61), (191, 62.7),
         (240, 66), (286, 71), (326, 77), (333, 78.3))


def spline(points, parameters=None):
    return cq.Edge.makeSpline([cq.Vector(*point) for point in points], parameters=parameters)


def waterline(profile, length_scale, beam_scale, inset):
    z, aft, fore, half_beam, transom = profile
    # Move the section inwards in plan and upwards to set the bottom skin.
    # This is a matched loft, not a constant-normal-thickness shell.
    # Reduce the inset near the keel so the narrow first section stays valid.
    local_inset = inset * half_beam / (half_beam + 7)
    half_beam = half_beam * beam_scale - local_inset
    aft = aft * length_scale + inset * 1.3
    fore = fore * length_scale - inset * 1.3
    z += inset
    span = fore - aft
    shoulder = 0.047 * (1 - transom) + 0.019
    # Separate port/starboard curves and a short U-shaped transom give every
    # station the same edge order and keep the fore stem on the center plane.
    side = [
        (shoulder, transom),
        (0.11, 0.63 + 0.30 * transom),
        (0.23, 0.92 + 0.07 * transom),
        (0.38, 1),
        (0.53, 0.965),
        (0.68, 0.815),
        (0.81, 0.585),
        (0.92, 0.325),
        (0.979, 0.120),
        (1, 0),
    ]
    port = [(aft + span * x, half_beam * y, z) for x, y in side]
    starboard = [(x, -y, z) for x, y, z in port]
    stern = [starboard[0],
             (aft + span * shoulder * 0.36, -half_beam * transom * 0.60, z),
             (aft, 0, z),
             (aft + span * shoulder * 0.36, half_beam * transom * 0.60, z),
             port[0]]
    side_parameters = [x for x, _ in side]
    stern_parameters = [y / (half_beam * transom) for _, y, _ in stern]
    return cq.Wire.assembleEdges([spline(port, side_parameters),
                                  spline(starboard, side_parameters),
                                  spline(stern, stern_parameters)])


def loft(length_scale, beam_scale, inset=0):
    builder = BRepOffsetAPI_ThruSections(True, False, 1e-6)
    builder.SetMaxDegree(3)
    for profile in WATERLINES:
        builder.AddWire(waterline(profile, length_scale, beam_scale, inset).wrapped)
    builder.Build()
    solid = cq.Shape.cast(builder.Shape())
    if not solid.isValid():
        raise RuntimeError("Waterlines did not produce a valid loft")
    return solid


def sheer_tool(length_scale, beam_scale):
    """A transverse extrusion whose lower edge is the sheer curve."""
    side_y = -100 * beam_scale
    curve = [(x * length_scale, side_y, z) for x, z in SHEER]
    aft, fore = curve[0], curve[-1]
    top_aft = (aft[0], side_y, 110)
    top_fore = (fore[0], side_y, 110)
    edges = [spline(curve)]
    edges.extend(cq.Edge.makeLine(cq.Vector(*p), cq.Vector(*q))
                 for p, q in [(fore, top_fore), (top_fore, top_aft), (top_aft, aft)])
    return cq.Solid.extrudeLinear(cq.Wire.assembleEdges(edges), [], cq.Vector(0, -2 * side_y, 0))


def make_hull(length_scale=1.0, beam_scale=1.0, skin=3.2):
    """Return the open hull; scale its plan without moving its keel datum."""
    if min(length_scale, beam_scale) <= 0 or not 0 < skin < 6:
        raise ValueError("Scales must be positive and skin must be between 0 and 6 mm")
    outer = loft(length_scale, beam_scale)
    inner = loft(length_scale, beam_scale, skin)
    return outer.cut(sheer_tool(length_scale, beam_scale)).cut(inner).clean()


def verify(hull):
    assert hull.isValid() and len(hull.Solids()) == 1
    box = hull.BoundingBox()
    solid = hull.Solids()[0]
    assert solid.isInside((145, 0, 3.15), 1e-6), "keel skin missing"
    assert not solid.isInside((145, 0, 3.25), 1e-6), "cavity floor is too high"
    assert not solid.isInside((145, 0, 50), 1e-6), "cavity is not open"
    for sign in (-1, 1):
        assert solid.isInside((140, sign * .475 * box.ylen, 50), 1e-6), "side wall missing"
    assert math.isclose(box.zmin, 0, abs_tol=1e-5)
    return (box.xlen, box.ylen, box.zlen, hull.Volume())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "boat-hull.step")
    args = parser.parse_args()
    hull = make_hull()
    baseline = verify(hull)
    cq.exporters.export(hull, str(args.output))
    saved = verify(cq.importers.importStep(str(args.output)).val())
    assert all(math.isclose(a, b, rel_tol=1e-5) for a, b in zip(baseline, saved))
    wider = verify(make_hull(beam_scale=1.1))
    assert wider[1] > 1.09 * saved[1]
    assert math.isclose(wider[0], saved[0], rel_tol=1e-4)
    assert math.isclose(wider[2], saved[2], rel_tol=1e-4)
    print("STEP X, Y, Z (mm), material volume (mm³):", tuple(round(x, 3) for x in saved))
    print("10% beam rebuild:", tuple(round(x, 3) for x in wider))
