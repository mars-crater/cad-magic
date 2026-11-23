"""Parametric banana loft from picked side-view contours. Millimetres."""
import argparse
from math import cos, pi, sin
from pathlib import Path

import cadquery as cq

# Projected length estimate only; the source photo has no physical scale.
MM_PER_PIXEL = 0.45
# Photo datum fixed at center of the stem cut. XY is the silhouette plane.
DATUM = (64, 107)
# (Inner / concave side, outer / convex side), in source-image coordinates.
# Paired points define both the section centerline and its local plane.
STATIONS = [
    ((77, 102), (51, 112)),
    ((77, 110), (52, 115)),
    ((77.33, 117.21), (52.58, 120.76)),
    ((79.31, 128.91), (55.59, 132.58)),
    ((81.46, 140.46), (58.57, 144.49)),
    ((85.12, 151.57), (60.64, 156.68)),
    ((88.4, 162.19), (61.67, 169.64)),
    ((94.66, 170.32), (59.57, 185.54)),
    ((101.31, 177.79), (55.64, 204.68)),
    ((109.87, 184.55), (56.04, 222.31)),
    ((126.1, 198.67), (66.81, 251.25)),
    ((142.23, 211.66), (85.55, 275.34)),
    ((159.4, 223.02), (108.74, 294.97)),
    ((178.49, 231.15), (134.65, 310.04)),
    ((198.59, 235.69), (162.76, 320.15)),
    ((218, 239.53), (191.62, 327.41)),
    ((243.79, 241.65), (238.41, 332.49)),
    ((261, 241.33), (269.1, 330.36)),
    ((280.99, 239.68), (296.59, 325.27)),
    ((301.79, 236.88), (323, 319.45)),
    ((323.07, 233.55), (348.54, 311.49)),
    ((344.32, 229.51), (373.13, 300.38)),
    ((366.23, 224.66), (395.7, 286.5)),
    ((390.72, 220.57), (415.2, 271.21)),
    ((403.77, 219.59), (423.96, 262.3)),
    ((416.34, 217.6), (432.44, 252.85)),
    ((425.5, 217.9), (436, 244.8)),
    ((429, 218), (438.5, 238)),
]


def section(inner, outer, depth_ratio, ridges):
    center_x = (inner[0] + outer[0]) / 2
    center_y = (inner[1] + outer[1]) / 2
    half_x = inner[0] - center_x
    half_y = inner[1] - center_y
    half_depth = (half_x**2 + half_y**2)**0.5 * depth_ratio
    points = []
    for i in range(48):
        angle = 2 * pi * i / 48
        # Modulate the unseen depth rather than moving the calibrated side outline.
        lobes = 1 + ridges * sin(angle)**2 * cos(5 * angle)
        points.append(cq.Vector(
            MM_PER_PIXEL * (center_x + half_x * cos(angle) - DATUM[0]),
            MM_PER_PIXEL * (DATUM[1] - center_y - half_y * cos(angle)),
            MM_PER_PIXEL * half_depth * sin(angle) * lobes,
        ))
    edge = cq.Edge.makeSpline(points, periodic=True)
    return cq.Wire.assembleEdges([edge])


def build(depth_ratio=0.77, ridges=0.075):
    if not 0.35 <= depth_ratio <= 1.25:
        raise ValueError('Depth ratio must be between 0.35 and 1.25')
    wires = [section(inner, outer, depth_ratio, ridges)
             for inner, outer in STATIONS]
    return cq.Solid.makeLoft(wires, ruled=False)


def verify(part):
    count = len(part.Solids())
    if count != 1 or not part.isValid() or part.Volume() <= 0:
        raise ValueError(f'Expected one valid positive-volume solid, got {count}')
    bounds = part.BoundingBox()
    return bounds.xlen, bounds.ylen, bounds.zlen, part.Volume()


def read_step(path):
    return cq.importers.importStep(str(path)).val()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--depth-ratio', type=float, default=0.77)
    parser.add_argument('--output', type=Path, default=Path('banana.step'))
    args = parser.parse_args()
    part = build(args.depth_ratio)
    source = verify(part)
    cq.exporters.export(part, str(args.output))
    reread = verify(read_step(args.output))
    assert all(abs(a-b) < 0.01 for a, b in zip(source, reread)), (source, reread)
    print(f'{args.output}: one valid solid before and after STEP round trip; '
          f'XYZ = {reread[:3]} mm; volume = {reread[3]:.3f} mm³')
