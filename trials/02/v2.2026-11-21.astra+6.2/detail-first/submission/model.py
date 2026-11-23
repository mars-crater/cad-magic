"""Run from the assignment folder: .venv/bin/python submission/model.py coupon|final"""
import sys, math
from pathlib import Path
from io import BytesIO
import cadquery as cq
import numpy as np, cv2, cairosvg
from PIL import Image
out=Path(__file__).resolve().parent
rgb=np.array(Image.open(BytesIO(cairosvg.svg2png(url=str(out/'reference.svg'),output_width=960,output_height=1080))).convert('RGB')).astype(float)
colors=np.array([[255,255,255],[39,57,71],[152,100,56]])
labels=np.argmin(((rgb[:,:,None]-colors)**2).sum(axis=3),axis=2)
scale=0.44/6
def xy(p):return ((p[0]-480)*scale,(540-p[1])*scale)
def slab(mask,z,h):
    contours,tree=cv2.findContours(mask.astype('uint8'),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    def wire(c):
        pts=cv2.approxPolyDP(c,0.75,True).reshape(-1,2)
        return cq.Wire.makePolygon([cq.Vector(*xy(p),z) for p in pts],close=True)
    solids=[]
    for i,c in enumerate(contours):
        if tree[0,i,3]!=-1 or cv2.contourArea(c)<6:continue
        holes=[wire(b) for j,b in enumerate(contours) if tree[0,j,3]==i and cv2.contourArea(b)>6]
        solids.append(cq.Solid.extrudeLinear(wire(c),holes,(0,0,h)))
    return solids
coupon=sys.argv[1]=='coupon'
if coupon:
    base=cq.Workplane('XY').center(0,3.0).rect(13,11).extrude(2.4).val()
else:
    # Rounded rectangular backing, overall height 78; emblem retains supplied aspect ratio.
    base=cq.Workplane('XY').box(60,78,2.4,centered=(True,True,False)).edges('|Z').fillet(8).val()
parts=[]
for label,height in [(1,.85),(2,1.4)]:
    for p in slab(labels==label,2.4,height):
        if coupon:
            p=p.intersect(base.translate((0,0,2.4)))
            if not p.Solids():continue
        parts.extend(p.Solids())
s=base.fuse(*parts).clean()
if not coupon:
    s=s.cut(cq.Solid.makeCylinder(2.4,6,(0,29.04,-1))).clean()
stem='coupon' if coupon else 'final'
cq.exporters.export(s,str(out/(stem+'.step')))
s=cq.importers.importStep(str(out/(stem+'.step'))).val()
b=s.BoundingBox()
print(stem,'solids',len(s.Solids()),'valid',s.isValid(),'bounds',b.xlen,b.ylen,b.zlen)
if not coupon:
    for z in [.1,1.2,2.39]:
        print('bore section',z,'center empty',not s.isInside((0,29.04,z)),'wall solid',s.isInside((2.45,29.04,z)))
