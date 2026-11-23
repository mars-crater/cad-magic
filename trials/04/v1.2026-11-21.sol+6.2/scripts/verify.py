"""Check the saved STEP, and rebuild with a changed driving diameter."""
from dataclasses import replace
from pathlib import Path

import cadquery as cq
import numpy as np
from scipy.spatial import cKDTree
from OCP.gp import gp_Pnt, gp_Vec

from adaptor import Dimensions, build


def skins(part):
    profiles = [face._geomAdaptor() for face in part.Faces() if face.geomType() == "BSPLINE"]
    return sorted(profiles, reverse=True, key=lambda s: s.Value(0, s.Bounds()[2]).Y())


def section(surface, u, count=8192):
    _, _, v0, v1 = surface.Bounds()
    return np.array([surface.Value(u, v).Coord() for v in np.linspace(v0, v1, count, endpoint=False)])


def dimensions(points):
    extent = np.ptp(points, axis=0)
    center = (points.max(axis=0) + points.min(axis=0)) / 2
    return extent[1], extent[2], center[2]


def verify(part, d):
    assert part.isValid() and len(part.Solids()) == 1 and part.Volume() > 0
    assert abs(part.BoundingBox().xlen - d.length) < 0.001
    assert len(part.Faces()) == 4, "Expected two skins and two open-end rings"
    outer, inner = skins(part)
    stations = [
        (0, (d.inlet_diameter, d.inlet_diameter, 0)),
        (d.ellipse_x, (d.ellipse_width, d.ellipse_height, d.ellipse_rise)),
        (d.length, (d.mouth_width, d.mouth_height, 0)),
    ]
    for x, target in stations:
        o, i = [section(s, x / d.length) for s in (outer, inner)]
        assert np.allclose(o[:, 0], x, atol=2e-5)
        assert np.allclose(dimensions(o), target, atol=0.001)
        assert np.allclose(dimensions(i), (target[0]-2*d.wall, target[1]-2*d.wall, target[2]), atol=0.001)
        sizes = [" × ".join(f"{value:.4f}" for value in dimensions(points)[:2]) for points in (o, i)]
        print(f"X={x}: outer {sizes[0]}; bore {sizes[1]}; Z center {dimensions(o)[2]:.4f}")
        if x < d.length:
            normalized = (o[:, 1:] - [0, target[2]]) / (np.array(target[:2]) / 2)
            residual = abs(np.linalg.norm(normalized, axis=1) - 1).max()
            assert residual * max(target[:2]) / 2 < 0.001
    o, i = [section(s, 1)[:, 1:] for s in (outer, inner)]
    flat_span = np.array([d.mouth_width/2-d.corner_radius, d.mouth_height/2-d.corner_radius])
    for points, radius in [(o, d.corner_radius), (i, d.corner_radius-d.wall)]:
        error = abs(np.linalg.norm(np.maximum(abs(points) - flat_span, 0), axis=1) - radius).max()
        assert error < 0.001
        print(f"Mouth profile max deviation from R{radius:g} rounded rectangle: {error:.6f} mm")
    min_clearance = []
    for u in np.linspace(0, 1, 17):
        o, i = [section(s, u)[:, 1:] for s in (outer, inner)]
        min_clearance.append(cKDTree(i).query(o)[0].min())
        x = u * d.length
        if 0 < u < 1:
            center_z = dimensions(section(inner, u))[2]
            assert not part.isInside((x, 0, center_z))
    print(f"Minimum in-plane wall at 17 sampled stations: {min(min_clearance):.3f}–{max(min_clearance):.3f} mm")
    assert max(abs(value - d.wall) for value in min_clearance) < 0.02
    for surface in (outer, inner):
        _, _, v0, v1 = surface.Bounds()
        for u in np.linspace(0, 1, 9):
            first, last = gp_Vec(), gp_Vec()
            surface.D1(u, v0, gp_Pnt(), gp_Vec(), first)
            surface.D1(u, v1, gp_Pnt(), gp_Vec(), last)
            assert first.Angle(last) < 1e-5


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    nominal = Dimensions()
    verify(cq.importers.importStep(str(root / "results" / "vacuum-adaptor.step")).val(), nominal)
    edited = replace(nominal, inlet_diameter=44)
    verify(build(edited), edited)
