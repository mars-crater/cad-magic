#!/usr/bin/env python3
"""Parametric visual study; millimetres. Rebuild with cad-magic venv."""
import math, os, sys
import cadquery as cq
from cadquery import exporters

N=int(os.getenv('WINGS','6'))
HUB_R=float(os.getenv('HUB_R','23'))
WING_END=float(os.getenv('WING_END','81'))
OUT=os.path.dirname(os.path.abspath(__file__))

def build():
    parts=[]
    # Hub and concentric raised rings, distinct parts in the exported compound.
    parts.append(cq.Workplane('XY').polygon(N,2*HUB_R/math.cos(math.pi/N)).extrude(5).val())
    parts.append(cq.Workplane('XY').circle(20).circle(17.8).extrude(1.2).translate((0,0,5)).val())
    ring=cq.Workplane('XY').circle(17.7).circle(15.0).extrude(1.0).translate((0,0,5))
    # Decorative bolt perforations as real blind openings in the raised annulus.
    for i in range(36):
        a=2*math.pi*i/36
        cutter=cq.Workplane('XY').center(16.5*math.cos(a),16.5*math.sin(a)).circle(.43).extrude(2).translate((0,0,5))
        ring=ring.cut(cutter)
    parts.append(ring.val())
    # Truncated domed centre; circular loft approximates the visible rounded cap.
    cap=(cq.Workplane('XY').workplane(offset=5).circle(14.7)
         .workplane(offset=1).circle(14.4).workplane(offset=2).circle(12.5)
         .workplane(offset=1.6).circle(8.6).loft(combine=True))
    parts.append(cap.val())
    parts.append(cq.Workplane('XY').circle(7.0).circle(6.8).extrude(.18).translate((0,0,9.55)).val())
    for i in range(N):
        angle=360*i/N
        # Wing starts under hub; tapered toward rolled tip. Three engraved bands.
        wing=(cq.Workplane('XY').polyline([(19,-7),(WING_END,-5.8),(WING_END,5.8),(19,7)]).close().extrude(2.6).translate((0,0,1)))
        for x in (51,60,69):
            wing=wing.cut(cq.Workplane('XY').box(.65,18,.35).translate((x,0,3.5)))
        parts.append(wing.val().rotate((0,0,0),(0,0,1),angle))
        # tip bar oriented tangentially
        tip=cq.Solid.makeCylinder(1.4,13,cq.Vector(WING_END,-6.5,2.3),cq.Vector(0,1,0))
        parts.append(tip.rotate((0,0,0),(0,0,1),angle))
        # Pod offset to one side of each wing, radial axis, open outward end.
        body=cq.Solid.makeCylinder(4.2,15,cq.Vector(38,-11,-1.3),cq.Vector(1,0,0))
        bore=cq.Solid.makeCylinder(3.1,5,cq.Vector(48.1,-11,-1.3),cq.Vector(1,0,0))
        pod=body.cut(bore)
        parts.append(pod.rotate((0,0,0),(0,0,1),angle))
        support=cq.Workplane('XY').box(6,7,3).translate((42,-7.8,.1)).val()
        parts.append(support.rotate((0,0,0),(0,0,1),angle))
    return cq.Compound.makeCompound(parts)

if __name__=='__main__':
    shape=build(); exporters.export(shape,os.path.join(OUT, 'spinner.step'))
    print('exported',len(shape.Solids()), 'valid',shape.isValid())
