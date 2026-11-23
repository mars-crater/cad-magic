"""Estimated lower-right wing unit, dimensions in mm. Rebuild with CadQuery 2.8."""
import os
import cadquery as cq
from cadquery import exporters
from pathlib import Path
P=Path(__file__).resolve().parent
SPAN=float(os.environ.get('WING_SPAN', '110.0'))
# Planform: outboard direction +X; chord direction Y; top +Z.
# Reference shows the nacelle ahead of the leading edge, suspended under the inboard half;
# tip rail runs across the chord, not along the span.
wing=(cq.Workplane('XY').polyline([(0,-20),(0,20),(SPAN,14),(SPAN,-13)]).close().extrude(5))
# A subtle upper crown keeps the main lifting surface legible.
# Two narrow recessed panel lines transverse to span, matching the visible divisions.
for x in (69,91):
    cutter=cq.Workplane('XY').box(.65,60,.32).translate((x,0,4.9))
    wing=wing.cut(cutter)
# Wingtip rail is a cross-chord capsule, slightly offset below the wing top.
rail=(cq.Workplane('XZ',origin=(SPAN+2,-18,2)).circle(2.3).extrude(-35))
# The Workplane XZ positive normal is -Y, so negative extrusion extends toward +Y.
# Nacelle cylindrical pod parallel to chord; front opening faces -Y.
x=55
outer=cq.Workplane('XZ',origin=(x,-51,-9)).circle(9.5).extrude(-32)
bore=cq.Workplane('XZ',origin=(x,-51.1,-9)).circle(7.3).extrude(-7)
pod=outer.cut(bore)
# Rear taper from full-diameter barrel to a smaller rear cap.
taper=(cq.Workplane('XZ',origin=(x,-19,-9)).circle(9.5).workplane(offset=-8).circle(5.5).loft())
pod=pod.union(taper)
# Pylon runs from the upper nacelle into underside of wing.
pylon=(cq.Workplane('YZ',origin=(x-2.4,0,0)).polyline([(-26,-4),(-13,0),(1,0),(-19,-9)]).close().extrude(4.8))
# Parts are exported as separate solids, preserving the visible assembly boundaries.
parts=[wing.val(),rail.val(),pod.val(),pylon.val()]
result=cq.Compound.makeCompound(parts)
exporters.export(result,str(P/'wing.step'))
