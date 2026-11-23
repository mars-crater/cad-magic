#!/tmp/cad-magic-venv/bin/python
"""Parametric rotary dial. Run: python dial.py [slot-count] [output.step]."""
import math
import sys
import cadquery as cq

DIAMETER = 64.0
THICKNESS = 6.0
BORE_DIAMETER = 8.0
SLOT_LENGTH = 10.0  # overall end-to-end length
SLOT_WIDTH = 3.0
SLOT_DEPTH = 2.0
SLOT_RADIUS = 23.0

def make_dial(count=8):
    disk = cq.Workplane('XY').circle(DIAMETER / 2).extrude(THICKNESS)
    disk = disk.faces('>Z').workplane().hole(BORE_DIAMETER)
    # Each capsule is built on the same top plane. slot2D's length is overall.
    for i in range(count):
        a = 360.0 * i / count
        x = SLOT_RADIUS * math.cos(math.radians(a))
        y = SLOT_RADIUS * math.sin(math.radians(a))
        disk = disk.faces('>Z').workplane(centerOption='CenterOfBoundBox').center(x, y).slot2D(SLOT_LENGTH, SLOT_WIDTH, a).cutBlind(-SLOT_DEPTH)
    return disk

if __name__ == '__main__':
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    output = sys.argv[2] if len(sys.argv) > 2 else f'dial_{count}.step'
    cq.exporters.export(make_dial(count), output)
