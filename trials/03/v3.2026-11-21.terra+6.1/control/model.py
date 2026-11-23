import cadquery as cq
from cadquery import Vector
from pathlib import Path
import math, os
P=Path(__file__).resolve().parent
# All dimensions estimated in mm from a single perspective image.
SPAN=float(os.getenv('WING_SPAN','180'))
def section(x, lead, chord, thick):
    # Rounded airfoil: leading edge at y=lead, trailing edge at lead+chord.
    pts=[]
    for i in range(31):
        t=i/30
        z=thick*(0.2969*math.sqrt(t)-0.126*t-0.3516*t*t+0.2843*t**3-0.1015*t**4)/0.2
        pts.append(Vector(x,lead+chord*t,z))
    for i in range(29,0,-1):
        t=i/30
        z=-thick*.55*(0.2969*math.sqrt(t)-0.126*t-0.3516*t*t+0.2843*t**3-0.1015*t**4)/0.2
        pts.append(Vector(x,lead+chord*t,z))
    return cq.Wire.assembleEdges([cq.Edge.makeSpline(pts, periodic=True)])
wires=[section(0,0,76,11),section(SPAN*.55,12,63,9),section(SPAN,25,48,6)]
wing=cq.Solid.makeLoft(wires)
# Two shallow panel lines on the upper face, with material retained below.
for x in (SPAN*.55,SPAN*.78):
    cutter=cq.Workplane('XY').box(1.2,110,1.0).translate((x,38,5.2)).val()
    wing=wing.cut(cutter)
# Underwing nacelle, axis parallel to airflow (Y). Open front lip and recessed intake.
x=SPAN*.39
outer=cq.Solid.makeCylinder(17,68,Vector(x,-26,-24),Vector(0,1,0))
front=cq.Solid.makeCone(13,17,10,Vector(x,-36,-24),Vector(0,1,0))
rear=cq.Solid.makeCone(17,12,12,Vector(x,42,-24),Vector(0,1,0))
engine=outer.fuse(front,rear)
engine=engine.cut(cq.Solid.makeCylinder(11.2,15,Vector(x,-36.01,-24),Vector(0,1,0)))
# Narrow ring groove near the front, gives nacelle panel break.
ring=cq.Solid.makeCylinder(17.1,0.8,Vector(x,-18,-24),Vector(0,1,0)).cut(cq.Solid.makeCylinder(16.4,0.8,Vector(x,-18,-24),Vector(0,1,0)))
engine=engine.cut(ring)
# Pylon bridges nacelle and underside of wing.
pylon=cq.Workplane('XY').box(10,38,20).translate((x,20,-10)).val()
# Tip rail: thin rounded cylindrical bar along the chord.
rail=cq.Solid.makeCylinder(4.2,48,Vector(SPAN+3,25,0),Vector(0,1,0)).fuse(cq.Solid.makeSphere(4.2,Vector(SPAN+3,25,0)),cq.Solid.makeSphere(4.2,Vector(SPAN+3,73,0)))
# Small tip bridge ensures attachment, like the end fitting in the reference.
bridge=cq.Workplane('XY').box(8,10,5).translate((SPAN,48,0)).val()
model=cq.Compound.makeCompound([wing,engine,pylon,rail,bridge])
cq.exporters.export(model,str(P/'wing.step'))
print('exported', P/'wing.step')
