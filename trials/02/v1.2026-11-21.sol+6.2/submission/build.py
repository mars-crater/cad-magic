"""Rebuild both reliefs from the supplied PNG references. All CAD units are mm."""
from pathlib import Path
import argparse

import cadquery as cq
import contourpy
import cv2
import numpy as np
from PIL import Image

from terrain_mesh import constrained_triangles, terrain_solid

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
MADEIRA_WIDTH = 145.0
MADEIRA_RELIEF = 25.0
MADEIRA_BASE = 3.0
CREST_WIDTH = 60.0
CREST_BASE = 2.5
FIELD_HEIGHT = 0.65
GOLD_HEIGHT = 1.35
LOOP_OD = 11.0
BORE = 5.0


def contours(mask, epsilon, minimum_area):
    # Marching squares separates diagonal neighbors without self-touching vertices.
    generator = contourpy.contour_generator(z=mask.astype(float), fill_type='OuterOffset')
    polygons, offsets = generator.filled(0.5, 1.5)
    for loops, bounds in zip(polygons, offsets):
        paths = []
        for start, end in zip(bounds, bounds[1:]):
            loop = loops[start:end - 1].astype(np.float32)
            if cv2.contourArea(loop) < minimum_area:
                if start == 0:
                    break
                continue
            simplified = cv2.approxPolyDP(loop, epsilon, True).reshape(-1, 2)
            if len(simplified) >= 3:
                paths.append(simplified)
            elif start == 0:
                break
        if paths:
            yield paths[0], paths[1:]


def prism(path, holes, transform, bottom, top):
    def wire(points):
        return cq.Wire.makePolygon([cq.Vector(*transform(x, y), bottom)
                                    for x, y in points], close=True)

    return cq.Solid.extrudeLinear(wire(path), [wire(hole) for hole in holes],
                                  (0, 0, top - bottom))


def madeira_source(width):
    gray = np.asarray(Image.open(ROOT / 'inputs/madeira.png').convert('L'))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    land = cv2.morphologyEx(np.uint8(gray > 2), cv2.MORPH_CLOSE, kernel)
    outline, _ = max(contours(np.pad(land, 1), 0.56, 30),
                     key=lambda p: cv2.contourArea(p[0]))
    outline -= 1  # Undo the one-pixel contour padding.
    outside = np.array([
        a + fraction * (b - a)
        for a, b in zip(outline, np.roll(outline, -1, axis=0))
        for fraction in np.linspace(
            0, 1, max(1, int(np.ceil(np.linalg.norm(b - a) / 3))), endpoint=False)
    ])
    pixel_mm = width / np.ptp(outside[:, 0])

    def transform(x, y):
        return ((x - (gray.shape[1] - 1) / 2) * pixel_mm,
                ((gray.shape[0] - 1) / 2 - y) * pixel_mm)

    return gray, outside, transform


def madeira(width=MADEIRA_WIDTH, relief=MADEIRA_RELIEF):
    gray, outside, transform = madeira_source(width)
    # Blur subpixel noise, not the broad ridges and drainage cuts.
    smoothed = cv2.GaussianBlur(gray.astype('float32'), (0, 0), 0.65)
    xy, triangles = constrained_triangles(outside, pitch=2.7)
    maps = [column.astype('float32').reshape((-1, 1)) for column in xy.T]
    sample = cv2.remap(smoothed, *maps, interpolation=cv2.INTER_LINEAR).ravel()
    z = MADEIRA_BASE + relief * sample / sample.max()
    return terrain_solid(np.column_stack([xy, z]), len(outside), triangles, transform)


def crest_source(width):
    rgba = np.asarray(Image.open(ROOT / 'crest.png').convert('RGBA'))
    rgba = np.pad(rgba, ((8, 8), (8, 8), (0, 0)))
    opaque = rgba[:, :, 3] >= 128
    gold = opaque & (rgba[:, :, 1] >= 112) & (rgba[:, :, 0] >= 143)
    h, w = opaque.shape
    pixel_mm = width / (np.ptp(np.where(opaque)[1]))

    def transform(x, y):
        return ((x - (w - 1) / 2) * pixel_mm,
                ((h - 1) / 2 - y) * pixel_mm)

    return opaque, gold, transform


def crest(width=CREST_WIDTH, bore=BORE):
    opaque, gold, transform = crest_source(width)
    # Outer backing overlaps adjoining crest elements; its rim is lower than the image.
    spread = cv2.dilate(np.uint8(opaque), cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (9, 9)))
    outside, holes = max(contours(spread, 0.52, 30),
                         key=lambda p: cv2.contourArea(p[0]))
    projected = [transform(x, y) for x, y in outside]
    crown = max(y for x, y in projected)
    ring_x, ring_y = 0.0, crown + 6.9
    deck = prism(outside, holes, transform, 0, CREST_BASE)
    # Separate short tab keeps the bore above the artwork. The tab and ring overlap.
    stem = cq.Solid.makeBox(5.5, 4.0, CREST_BASE, cq.Vector(-2.75, crown - 1.5, 0))
    ring = cq.Solid.makeCylinder(LOOP_OD / 2, CREST_BASE,
                                cq.Vector(ring_x, ring_y, 0))
    through = cq.Solid.makeCylinder(bore / 2, CREST_BASE + 2,
                                   cq.Vector(ring_x, ring_y, -1))
    deck = deck.fuse(stem, ring).cut(through)
    levels = []
    for mask, height, eps, area in [(opaque, FIELD_HEIGHT, 0.38, 8),
                                    (gold, GOLD_HEIGHT, 0.38, 7)]:
        # Layers overlap the deck so fine marks do not depend on a touching-only union.
        for outline, inner in contours(mask, eps, area):
            piece = prism(outline, inner, transform, CREST_BASE - 0.05,
                          CREST_BASE + height)
            if not piece.isValid():
                raise ValueError(f'Invalid crest polygon near {outline.mean(axis=0)}')
            levels.append(piece)
    return deck.fuse(*levels).clean(), (ring_x, ring_y)


def save(shape, name):
    assert len(shape.Solids()) == 1 and shape.isValid()
    cq.exporters.export(shape, str(OUT / f'{name}.step'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('part', choices=('madeira', 'crest', 'both'), default='both', nargs='?')
    args = parser.parse_args()
    if args.part in ('madeira', 'both'):
        save(madeira(), 'madeira')
    if args.part in ('crest', 'both'):
        save(crest()[0], 'crest')
