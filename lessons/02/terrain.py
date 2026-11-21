"""Trace georeferenced Hawaiʻi Island elevation bands into periodic spline tiers."""
from math import asinh, pi, radians, tan
from pathlib import Path

import cadquery as cq
import numpy as np
from contourpy import contour_generator
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

from terrain_input import LEFT, TOP, WIDTH, HEIGHT, ZOOM

HERE = Path(__file__).resolve().parent
MM_PER_PIXEL = 0.4
LAYER = 1.5
LEVELS = (20, 500, 1000, 1500, 2000, 2500, 3000, 3500, 3800)
PALETTE = ["#94bfa5", "#82af82", "#759662", "#a6a45f", "#bcad6f",
           "#c69f74", "#af815f", "#947265", "#d6c8ad"]


def elevation():
    return np.asarray(Image.open(HERE / "terrain-dem.png")).astype(float)


def xy(pixel):
    col, row = pixel
    return ((col - WIDTH / 2) * MM_PER_PIXEL, (HEIGHT / 2 - row) * MM_PER_PIXEL)


def contours(grid, threshold):
    for ring in contour_generator(z=grid).lines(threshold):
        # Positive-elevation islands have positive orientation in raster coordinates.
        twice_area = np.sum(ring[:-1, 0] * ring[1:, 1] - ring[1:, 0] * ring[:-1, 1])
        if twice_area < 24 or not np.allclose(ring[0], ring[-1]):
            continue
        arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ring, axis=0), axis=1))]
        distances = np.linspace(0, arc[-1], max(10, round(arc[-1] / 3)), endpoint=False)
        yield np.column_stack([np.interp(distances, arc, column) for column in ring.T])


def build():
    raw = elevation()
    reference = Image.new("RGB", (WIDTH, HEIGHT), "#e7f0f3")
    smooth = gaussian_filter(raw, 0.75)
    relief = cq.Workplane("XY")
    for level, (threshold, color) in enumerate(zip(LEVELS, PALETTE)):
        reference.paste(color, mask=Image.fromarray(raw >= threshold))
        for points in contours(smooth, threshold):
            tier = (cq.Workplane("XY", origin=(0, 0, LAYER * level))
                    .spline([xy(point) for point in points], periodic=True)
                    .close().extrude(LAYER))
            relief = relief.union(tier)
    reference.save(HERE / "terrain-reference.png")
    return relief


def location(lon, lat):
    world = 256 * 2 ** ZOOM
    pixel = ((lon + 180) / 360 * world - LEFT - 0.5,
             (1 - asinh(tan(radians(lat))) / pi) / 2 * world - TOP - 0.5)
    return xy(pixel)


def verify(result):
    solid = result.val()
    assert len(result.solids().vals()) == 1 and solid.isValid()
    assert abs(solid.BoundingBox().zlen - len(LEVELS) * LAYER) < 1e-4
    raw = elevation()
    overlaps = []
    for index, threshold in enumerate(LEVELS):
        section = result.section((index + 0.5) * LAYER)
        mask = Image.new("1", (WIDTH, HEIGHT))
        for wire in section.wires().vals():
            samples, _ = wire.sample(max(40, round(wire.Length() / 0.24)))
            pixels = [(round(v.x / MM_PER_PIXEL + WIDTH / 2),
                       round(HEIGHT / 2 - v.y / MM_PER_PIXEL)) for v in samples]
            ImageDraw.Draw(mask).polygon(pixels, fill=1)
        traced, source = np.asarray(mask), raw >= threshold
        overlap = np.count_nonzero(traced & source) / np.count_nonzero(traced | source)
        overlaps.append(overlap)
    print("Terrain band intersection/union vs DEM:", [round(float(n), 3) for n in overlaps])
    assert min(overlaps) > 0.85
    summits = [(-155.468, 19.821), (-155.608, 19.475)]
    for lon, lat in summits:
        assert solid.isInside(cq.Vector(*location(lon, lat), 12.75))
    assert not solid.isInside(cq.Vector(*location(-155.51, 19.69), 12.75))
