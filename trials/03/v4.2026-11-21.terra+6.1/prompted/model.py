import cadquery as cq, math, os, sys
from cadquery import exporters
N=int(os.getenv('ARM_COUNT','6')); OUT=os.path.dirname(__file__)
# Millimetres. Radial x, tangential y, vertical z. Station profiles approximate the image.
stations=[(19,15,0.0),(34,17,0.2),(49,18,0.8),(63,19,2.2),(71,19,5.2)]
def wire(x,w,z):
    return cq.Workplane('YZ',origin=(x,0,z)).rect(w,2.6).val()
arm=cq.Solid.makeLoft([wire(*p) for p in stations],True)
# Before repeating: save the unadorned seed for independent top/section inspection.
exporters.export(arm,OUT+'/seed.step')
# center: faceted body and raised concentric button
hub=cq.Workplane('XY').polygon(12,48).extrude(5).translate((0,0,-2.5)).val()
ring=cq.Workplane('XY').circle(20).circle(16.4).extrude(0.8).translate((0,0,2.5)).val()
button=cq.Workplane('XY').circle(16.4).extrude(1.0).translate((0,0,2.5)).edges('>Z').fillet(0.8).val()
cap=cq.Workplane('XY').circle(8).extrude(0.4).translate((0,0,3.5)).val()
parts=[hub,ring,button,cap]
# The separate parts deliberately remain an assembly-like compound, not a fused mechanism.
for i in range(N):
    a=360*i/N
    def rot(s): return s.rotate((0,0,0),(0,0,1),a)
    parts.append(rot(arm))
    # Rounded bar at tip, crosswise to radial axis
    tip=cq.Solid.makeCylinder(1.6,20,cq.Vector(71,-10,5.2),cq.Vector(0,1,0))
    parts.append(rot(tip))
    # Shallow transverse seams, represented as narrow surface strips.
    for x,z,w in [(43,2.0,17.5),(53,2.6,18.2),(62,3.5,18.8)]:
        strip=cq.Workplane('XY').box(0.5,w,0.22).translate((x,0,z)).val()
        parts.append(rot(strip))
    # nacelle: horizontal hollow tube below wing; axis radial
    outer=cq.Solid.makeCylinder(4.7,17,cq.Vector(27,-11,-4.2),cq.Vector(1,0,0))
    inner=cq.Solid.makeCylinder(3.5,17,cq.Vector(27,-11,-4.2),cq.Vector(1,0,0))
    parts.append(rot(outer.cut(inner)))
    # short pylon attaches pod visually to arm
    parts.append(rot(cq.Workplane('XY').box(8,3,5).translate((34,-8,-2)).val()))
model=cq.Compound.makeCompound(parts)
exporters.export(model,OUT+'/spinner.step')
print('exported',len(parts),'components; arms',N)
