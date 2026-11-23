"""Rebuild the exterior-study STEP in millimetres with CadQuery."""
from argparse import ArgumentParser
from dataclasses import dataclass
from math import cos, pi, sin
from pathlib import Path

import cadquery as cq


@dataclass(frozen=True)
class Design:
    arms: int = 6
    hub_flat_radius: float = 20.0
    tip_station: float = 60.0
    cap_radius: float = 13.4
    marks_per_sector: int = 6

    @property
    def pitch(self):
        return 360.0 / self.arms

    @property
    def span(self):
        return self.tip_station - self.hub_flat_radius


Z = (0, 0, 1)
ORIGIN = (0, 0, 0)
STEEL = (0.70, 0.78, 0.86)
BRIGHT = (0.79, 0.85, 0.90)
DARK = (0.18, 0.23, 0.30)
GOLD = (0.96, 0.59, 0.23)


def cylinder(radius, height, point, axis=Z):
    return cq.Solid.makeCylinder(radius, height, point, axis)


def polar(radius, degrees):
    radians = degrees * pi / 180
    return (radius * cos(radians), radius * sin(radians))


def frame_profile(design, apothem):
    radius = apothem / cos(pi / design.arms)
    return [polar(radius, (index + 0.5) * design.pitch) for index in range(design.arms)]


def polygon_loft(design, sections):
    wires = [
        cq.Workplane("XY", origin=(0, 0, z))
        .polyline(frame_profile(design, apothem)).close().val()
        for z, apothem in sections
    ]
    return cq.Solid.makeLoft(wires, ruled=True)


def wing(design):
    # X is radial, Y tangential. At the tip, the loft bends upward.
    # An elliptical airfoil has a real curved crown and a rounded underside.
    stations = [
        (-0.035, 6.05, 1.75, 0.00, 0.10),
        (0.20, 6.45, 1.62, -0.40, 0.16),
        (0.57, 6.80, 1.38, -1.15, 0.30),
        (0.84, 6.85, 1.16, -2.00, 0.80),
        (1.00, 6.95, 1.12, -2.70, 2.50),
    ]
    wires = [
        cq.Workplane("YZ", origin=(design.hub_flat_radius + fraction * design.span, y, z))
        .ellipse(half_width, half_height).val()
        for fraction, half_width, half_height, y, z in stations
    ]
    foil = cq.Solid.makeLoft(wires)
    # The panel grooves wrap the exposed crown while leaving the underside continuous.
    for fraction in (0.49, 0.63, 0.77):
        x = design.hub_flat_radius + fraction * design.span
        cutter = cq.Solid.makeBox(0.42, 24.0, 4.5, (x - 0.21, -14.0, 0.90))
        foil = foil.cut(cutter)
    tip = cylinder(1.22, 15.2, (design.tip_station - 0.15, -10.30, 2.50), (0, 1, 0))
    tip = tip.fuse(
        cq.Solid.makeSphere(1.22, (design.tip_station - 0.15, -10.30, 2.50),
                            (0, 0, 1), -90, 90),
        cq.Solid.makeSphere(1.22, (design.tip_station - 0.15, 4.90, 2.50),
                            (0, 0, 1), -90, 90),
    ).clean()
    return foil.fuse(tip).clean()


def pod(design):
    # Revolve the external bands and the stepped through-bore together.
    axis_profile = [
        (0.0, 3.20), (0.0, 3.90), (0.60, 4.48), (3.60, 4.53),
        (4.05, 4.55), (9.9, 4.32), (11.4, 4.08), (12.70, 3.62),
        (12.70, 2.50), (10.5, 2.46), (4.0, 2.64), (1.00, 3.15),
    ]
    shell = (
        cq.Workplane("XY").polyline(axis_profile).close()
        .revolve(360, (0, 0, 0), (1, 0, 0)).val()
        .rotate(ORIGIN, Z, 75)
        .translate((design.hub_flat_radius + 0.59 * design.span, -13.4, -5.42))
    )
    x = design.hub_flat_radius + 0.60 * design.span
    # A tapered pylon doubles as the short mount visible between blade and nacelle.
    pylon = (
        cq.Workplane("XY", origin=(x, -3.9, -0.34)).rect(5.0, 4.0)
        .workplane(offset=-2.65).center(-0.36, -2.0).rect(3.1, 5.45)
        .loft().val()
    )
    return shell, pylon


def build(design):
    assert 5 <= design.arms <= 7, "Supported study range: five to seven sectors"
    assert design.span >= 34, "Wing span must leave room for the pod and grooves"
    assert 11.0 <= design.cap_radius <= 13.5, "Cap must clear the decoration"
    core = polygon_loft(
        design, [(z, design.hub_flat_radius + delta)
                 for z, delta in [(-3.0, -0.75), (-2.25, 0.50),
                                  (1.35, 0.50), (2.0, -0.75)]]
    )
    deck = polygon_loft(design, [(2.0, design.hub_flat_radius - 0.75),
                                 (2.72, design.hub_flat_radius - 1.55)])
    # Main ring plus six lobes, indexed halfway between the arms.
    trim = cylinder(17.00, 0.50, (0, 0, 2.72))
    for index in range(design.arms):
        xy = polar(16.75, (index + 0.5) * design.pitch)
        trim = trim.fuse(cylinder(1.24, 0.50, (*xy, 2.72)))
    trim = trim.cut(cylinder(15.68, 0.60, (0, 0, 2.70))).clean()
    cap = cq.Workplane("XZ").moveTo(0, 2.72).lineTo(design.cap_radius, 2.72)
    cap = (cap.lineTo(design.cap_radius, 3.35)
           .spline([(design.cap_radius - 0.35, 4.35),
                    (design.cap_radius - 1.85, 5.75),
                    (design.cap_radius - 4.0, 6.95),
                    (design.cap_radius - 6.3, 7.35)], includeCurrent=True)
           .lineTo(design.cap_radius - 6.3, 7.12)
           .lineTo(design.cap_radius - 6.48, 7.12)
           .lineTo(design.cap_radius - 6.48, 7.35)
           .lineTo(0, 7.35).close().revolve().val())
    result = cq.Assembly(name="Spinner_exterior")

    def add(name, solid, color):
        result.add(solid, name=name, color=cq.Color(*color))

    add("faceted_frame", core, DARK)
    add("hub_crown", cap, GOLD)
    add("lobed_trim_ring", trim, GOLD)
    blade = wing(design)
    shell, pylon = pod(design)
    marks = []
    for index in range(design.arms):
        angle = index * design.pitch
        add(f"blade_{index+1}", blade.rotate(ORIGIN, Z, angle), STEEL)
        add(f"pylon_{index+1}", pylon.rotate(ORIGIN, Z, angle), STEEL)
        add(f"nacelle_{index+1}", shell.rotate(ORIGIN, Z, angle), BRIGHT)
        for mark_index in range(design.marks_per_sector):
            phase = (mark_index + 0.5) / design.marks_per_sector - 0.5
            for radius, size, z in ((14.68, 0.39, 2.80), (18.0, 0.36, 2.79)):
                point = polar(radius, angle + phase * design.pitch * 0.74)
                marks.append(cylinder(size, z - 2.60, (*point, 2.60)))
    deck = deck.cut(*marks).clean()
    add("upper_deck_with_mark_seats", deck, BRIGHT)
    # These separate pins seat in real shallow bores in the deck.
    for index, mark in enumerate(marks, start=1):
        center = mark.Center()
        pin = cylinder(0.34 if center.Length < 16 else 0.31, 0.23,
                       (center.x, center.y, 2.60))
        add(f"gold_mark_{index:02}", pin, GOLD)
    return result


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--arms", type=int, default=Design.arms)
    parser.add_argument("--tip", type=float, default=Design.tip_station)
    parser.add_argument("--cap-radius", type=float, default=Design.cap_radius)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("spinner.step"))
    args = parser.parse_args()
    design = Design(arms=args.arms, tip_station=args.tip, cap_radius=args.cap_radius)
    build(design).export(str(args.output), "STEP")
