#!/usr/bin/env python3
"""Parametric rotary indexing dial. All dimensions in millimetres."""
import argparse, math
from pathlib import Path
import cadquery as cq

DIAMETER = 64.0
THICKNESS = 6.0
BORE_DIAMETER = 8.0
SLOT_LENGTH = 10.0
SLOT_WIDTH = 3.0
SLOT_DEPTH = 2.0
SLOT_RADIUS = 23.0

def build(count=8):
    if count < 1:
        raise ValueError('count must be positive')
    dial = cq.Workplane('XY').circle(DIAMETER / 2).extrude(THICKNESS)
    dial = dial.faces('>Z').workplane().hole(BORE_DIAMETER)
    for i in range(count):
        angle = 360.0 * i / count
        rad = math.radians(angle)
        x, y = SLOT_RADIUS * math.cos(rad), SLOT_RADIUS * math.sin(rad)
        cutter = (cq.Workplane('XY').workplane(offset=THICKNESS-SLOT_DEPTH)
                  .center(x,y).slot2D(SLOT_LENGTH, SLOT_WIDTH, angle)
                  .extrude(SLOT_DEPTH))
        dial = dial.cut(cutter)
    return dial

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=8)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cq.exporters.export(build(args.count), str(args.output))
