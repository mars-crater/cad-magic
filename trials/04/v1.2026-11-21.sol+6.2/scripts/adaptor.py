"""Editable vacuum adaptor, dimensions in millimetres. Requires CadQuery 2.8."""
from dataclasses import dataclass
from math import atan2, cos, pi, sin
from pathlib import Path

import cadquery as cq
import numpy as np
from scipy.interpolate import make_interp_spline
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.Geom import Geom_BSplineSurface
from OCP.gp import gp_Pnt, gp_Vec
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.TColStd import TColStd_Array1OfInteger, TColStd_Array1OfReal


@dataclass(frozen=True)
class Dimensions:
    length: float = 80
    inlet_diameter: float = 40
    ellipse_x: float = 40
    ellipse_width: float = 42
    ellipse_height: float = 22
    ellipse_rise: float = 8
    mouth_width: float = 54
    mouth_height: float = 14
    corner_radius: float = 3
    wall: float = 2


def mouth_samples(d, inset, subdivisions=16):
    """Sample lines and circular corners with their exact tangent directions."""
    w, h, r = d.mouth_width / 2, d.mouth_height / 2, d.corner_radius
    for quarter, (cy, cz) in enumerate([(w-r, h-r), (-w+r, h-r), (-w+r, -h+r), (w-r, -h+r)]):
        angle = quarter * pi / 2
        direction = cq.Vector(0, -sin(angle), cos(angle))
        start = cq.Vector(0, cy + r * cos(angle), cz + r * sin(angle))
        line_length = 2 * (h-r) if quarter % 2 == 0 else 2 * (w-r)
        for i in range(subdivisions):
            point = start + direction * (line_length * (i / subdivisions - 1))
            inward = cq.Vector(0, -direction.z, direction.y)
            yield point, point + inset * inward, direction, line_length / subdivisions, i == 0
        for i in range(subdivisions):
            t = angle + pi * i / (2 * subdivisions)
            normal = cq.Vector(0, cos(t), sin(t))
            center = cq.Vector(0, cy, cz)
            tangent = cq.Vector(0, -sin(t), cos(t))
            yield center + r * normal, center + (r-inset) * normal, tangent, r * pi / (2 * subdivisions), True


def oval_sample(a, b, t, inset):
    """Position and angular derivative of a true planar inward offset."""
    point = cq.Vector(0, a*cos(t), b*sin(t))
    derivative = cq.Vector(0, -a*sin(t), b*cos(t))
    normal = cq.Vector(0, cos(t)/a, sin(t)/b).normalized()
    curvature = a*b / derivative.Length**3
    return point - inset * normal, derivative * (1-inset*curvature)


def station_samples(d, inset):
    stations = [[], [], []]
    steps = []
    w, h = d.mouth_width / 2, d.mouth_height / 2
    for outer, mouth, tangent, step, at_corner in mouth_samples(d, inset):
        y, z = outer.y / w, outer.z / h
        theta = atan2(z, y)
        rate = (y * tangent.z/h - z * tangent.y/w) / (y*y + z*z)
        for station, x, rise, a, b in [
            (stations[0], 0, 0, d.inlet_diameter/2, d.inlet_diameter/2),
            (stations[1], d.ellipse_x, d.ellipse_rise, d.ellipse_width/2, d.ellipse_height/2),
        ]:
            point, derivative = oval_sample(a, b, theta, inset)
            station.append((point + cq.Vector(x, 0, rise), derivative * rate))
        # The parallel corner has a smaller arc-length derivative than the outer.
        speed = (d.corner_radius-inset)/d.corner_radius if at_corner else 1
        stations[2].append((mouth + cq.Vector(d.length, 0, 0), tangent * speed))
        steps.append(step)
    return stations, steps


def bezier_controls(samples, steps):
    """Cubic Hermite segments; each node shares a first derivative."""
    controls = []
    for i, (point, tangent) in enumerate(samples):
        following, next_tangent = samples[(i + 1) % len(samples)]
        third = steps[i] / 3
        controls.extend((point, point + third*tangent, following - third*next_tangent))
    return controls + [samples[0][0]]


def knot_array(values, integral=False):
    cls = TColStd_Array1OfInteger if integral else TColStd_Array1OfReal
    result = cls(1, len(values))
    for index, value in enumerate(values, 1):
        result.SetValue(index, value)
    return result


def spline_surface(rows, u, u_multiplicities, u_degree, v):
    poles = TColgp_Array2OfPnt(1, len(rows), 1, len(rows[0]))
    for i, row in enumerate(rows, 1):
        for j, point in enumerate(row, 1):
            poles.SetValue(i, j, gp_Pnt(*point))
    return Geom_BSplineSurface(
        poles, knot_array(u), knot_array(v),
        knot_array(u_multiplicities, True),
        knot_array([4] + [3]*(len(v)-2) + [4], True),
        u_degree, 3,
    )


def exterior(d, stations, steps, v):
    start, mid, end = [bezier_controls(samples, steps) for samples in stations]
    t = d.ellipse_x / d.length
    control = [(b - (1-t)**2*a - t*t*c) / (2*t*(1-t)) for a, b, c in zip(start, mid, end)]
    rows = [[point.toTuple() for point in row] for row in (start, control, end)]
    return spline_surface(rows, [0., 1.], [3, 3], 2, v)


def offset_point(surface, u, v, wall):
    point, tangent = gp_Pnt(), gp_Vec()
    surface.D1(u, v, point, gp_Vec(), tangent)
    inward = cq.Vector(0, -tangent.Z(), tangent.Y()).normalized()
    return cq.Vector(point.Coord()) + wall * inward


def bore(d, outer, steps, v):
    # Interpolate cross-sectional offsets along X, rather than interpolating
    # three independently inset profiles and letting the wall thin between them.
    end_profiles, _ = station_samples(d, d.wall)
    sample_v = v[:-1]
    period = v[-1]
    epsilon = min(steps) * 1e-4
    axial = sorted({*np.linspace(0, 1, 25), d.ellipse_x / d.length})
    rows = []
    for u in axial:
        if u == 0:
            profile = end_profiles[0]
        elif u == 1:
            profile = end_profiles[-1]
        else:
            profile = []
            for parameter in sample_v:
                center = offset_point(outer, u, parameter, d.wall)
                past = offset_point(outer, u, (parameter + epsilon) % period, d.wall)
                prior = offset_point(outer, u, (parameter - epsilon) % period, d.wall)
                profile.append((center, (past - prior) / (2 * epsilon)))
        rows.append([point.toTuple() for point in bezier_controls(profile, steps)])
    fit = make_interp_spline(axial, rows)
    u, multiplicities = np.unique(fit.t, return_counts=True)
    return spline_surface(fit.c, u, [int(m) for m in multiplicities], fit.k, v)


def build(d=Dimensions()):
    stations, steps = station_samples(d, 0)
    v = [0.0, *np.cumsum(steps)]
    outer_surface = exterior(d, stations, steps, v)
    inner_surface = bore(d, outer_surface, steps, v)
    outer, inner = [cq.Face(BRepBuilderAPI_MakeFace(s, 1e-7).Face()) for s in (outer_surface, inner_surface)]
    ends = []
    for x in (0, d.length):
        outer_edge, = [e for e in outer.Edges() if abs(e.Center().x - x) < 1e-6]
        inner_edge, = [e for e in inner.Edges() if abs(e.Center().x - x) < 1e-6]
        ends.append(cq.Face.makeFromWires(cq.Wire.assembleEdges([outer_edge]), [cq.Wire.assembleEdges([inner_edge])]))
    return cq.Solid.makeSolid(cq.Shell.makeShell([outer, inner, *ends]))


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    part = build()
    print("valid", part.isValid(), "solids", len(part.Solids()), "faces", len(part.Faces()))
    cq.exporters.export(part, str(root / "results" / "vacuum-adaptor.step"))
