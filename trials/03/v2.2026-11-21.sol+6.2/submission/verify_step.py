"""Check the source and delivered STEP; rebuild a different five-sector design."""
from argparse import ArgumentParser
from math import cos, radians, sin
from pathlib import Path
from tempfile import TemporaryDirectory

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

from spinner import Design, ORIGIN, Z, build, polar


def collect(assembly):
    return {
        name.rsplit("/", 1)[-1]: shape.moved(location)
        for shape, name, location, _ in assembly
    }


def require(condition, description):
    if not condition:
        raise AssertionError(description)


def contains(shape, point):
    return shape.isInside(cq.Vector(*point), 1e-6)


def describe(parts, design, label):
    expected_solids = 4 + design.arms * (3 + 2 * design.marks_per_sector)
    all_solids = [solid for shape in parts.values() for solid in shape.Solids()]
    require(len(parts) == len(all_solids) == expected_solids, "Named solid count")
    require(all(solid.isValid() and solid.Volume() > 0 for solid in all_solids), "Invalid solid")
    cap = parts["hub_crown"]
    bounds = cap.BoundingBox()
    require(abs(bounds.xlen - 2 * design.cap_radius) < 0.002, "Cap diameter")
    cap_wall = max(
        (BRepAdaptor_Surface(face.wrapped).Cylinder()
         for face in cap.Faces() if face.geomType() == "CYLINDER"),
        key=lambda wall: wall.Radius(),
    )
    axis = cap_wall.Axis()
    require(abs(axis.Location().X()) < 1e-6 and abs(axis.Location().Y()) < 1e-6
            and abs(axis.Direction().Z()) > 0.999999, "Cap concentricity")
    base = parts["faceted_frame"]
    deck = parts["upper_deck_with_mark_seats"]
    require(abs(deck.Center().x) < 1e-5 and abs(deck.Center().y) < 1e-5, "Deck concentricity")
    require(abs(base.BoundingBox().xmax - design.hub_flat_radius - 0.5) < 0.002,
            "Hub radius across flats on one side")
    gaps = []
    seed_centers = {feature: parts[f"{feature}_1"].Center() for feature in
                    ("blade", "pylon", "nacelle")}
    for index in range(design.arms):
        angle = index * design.pitch
        blade, pylon, pod = [
            parts[f"{feature}_{index + 1}"].rotate(ORIGIN, Z, -angle)
            for feature in ("blade", "pylon", "nacelle")
        ]
        for feature, shape in zip(seed_centers, (blade, pylon, pod)):
            require((shape.Center() - seed_centers[feature]).Length < 1e-5,
                    f"{feature} {index + 1} spacing")
        require(abs(blade.BoundingBox().xmax - design.tip_station - 1.07) < 0.003,
                f"Blade {index + 1} tip station")
        for fraction in (0.49, 0.63, 0.77):
            station = design.hub_flat_radius + fraction * design.span
            require(not contains(blade, (station, -1.4, 1.27)), "Groove opens")
            require(contains(blade, (station + 0.55, -1.4, 1.27)), "Material beside groove")
            require(contains(blade, (station, -1.4, 0.70)), "Retained groove floor")
        for axial_station in (0.12, 6.35, 12.55):
            x = design.hub_flat_radius + 0.59 * design.span + axial_station * cos(radians(75))
            y = -13.4 + axial_station * sin(radians(75))
            require(not contains(pod, (x, y, -5.42)), "Open nacelle bore")
            require(contains(pod, (x, y, -1.95)), "Retained nacelle wall")
        neighbor = (index + 1) % design.arms
        gap = parts[f"blade_{index + 1}"].distance(parts[f"blade_{neighbor + 1}"])
        require(gap > 0.20, "Adjacent blades touch or overlap")
        gaps.append(gap)
        for mark_index in range(design.marks_per_sector):
            phase = (mark_index + 0.5) / design.marks_per_sector - 0.5
            for radius in (14.68, 18.0):
                x, y = polar(radius, angle + phase * design.pitch * 0.74)
                require(not contains(deck, (x, y, 2.66)), "Open mark seat")
                require(contains(deck, (x, y, 2.54)), "Retained mark seat floor")
    model = cq.Compound.makeCompound(list(parts.values()))
    box = model.BoundingBox()
    print(f"{label}: {len(parts)} nodes / {len(all_solids)} valid positive-volume solids; "
          f"XYZ envelope {box.xlen:.3f} × {box.ylen:.3f} × {box.zlen:.3f} mm")
    print(f"  {design.arms} sectors × {design.pitch:.2f}°; cap Ø{bounds.xlen:.3f} mm and concentric; "
          f"tip envelope local +X {design.tip_station + 1.07:.3f} mm")
    print(f"  Neighbor blade gaps {min(gaps):.3f} to {max(gaps):.3f} mm; "
          f"last-to-first {gaps[-1]:.3f} mm")
    print(f"  Passed: {3 * design.arms} groove/floor probes, "
          f"{3 * design.arms} nacelle bore/wall station probes, and "
          f"{2 * design.arms * design.marks_per_sector} shallow seat/floor probes.")


def compare(source, imported):
    require(set(source) == set(imported), "STEP names differ")
    volume_delta = max(abs(shape.Volume() - imported[name].Volume())
                       for name, shape in source.items())
    require(volume_delta < 0.005, "STEP round trip exceeds volume tolerance")
    print(f"  Source-to-STEP maximum per-solid volume delta: {volume_delta:.7f} mm³")


def verify(step):
    design = Design()
    source = collect(build(design))
    imported = collect(cq.Assembly.importStep(str(step)))
    print(f"CadQuery {cq.__version__}")
    describe(source, design, "Nominal source")
    describe(imported, design, "Nominal STEP")
    compare(source, imported)
    changed = Design(arms=5, tip_station=64.0, cap_radius=12.6)
    with TemporaryDirectory() as temporary:
        target = Path(temporary) / "adjusted.step"
        variant = build(changed)
        variant.export(str(target), "STEP")
        source = collect(variant)
        imported = collect(cq.Assembly.importStep(str(target)))
        describe(source, changed, "Edited source")
        describe(imported, changed, "Edited STEP")
        compare(source, imported)


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("step", type=Path)
    verify(parser.parse_args().step)
