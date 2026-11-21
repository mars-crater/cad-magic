"""Build from trial-local image references; all dimensions in millimetres."""
from pathlib import Path
import sys
import cadquery as cq
import cv2
import numpy as np
from PIL import Image
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.gp import gp_Vec

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent

def profiles(mask, scale, z, epsilon, minimum=1):
    contours, tree = cv2.findContours(mask.astype('uint8'),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    def wire(c):
        points=cv2.approxPolyDP(c,epsilon,True)[:,0]
        if len(points)<3: return None
        return cq.Wire.makePolygon([cq.Vector(float(x)*scale,-float(y)*scale,z) for x,y in points],close=True)
    faces=[]
    for i,c in enumerate(contours):
        if tree[0,i,3]>=0 or cv2.contourArea(c)<minimum: continue
        w=wire(c)
        if w is None: continue
        holes=[wire(contours[j]) for j in np.where(tree[0,:,3]==i)[0] if cv2.contourArea(contours[j])>=minimum]
        faces.append(cq.Face.makeFromWires(w,[h for h in holes if h is not None]))
    return faces

def prism(face,dz):
    return cq.Shape.cast(BRepPrimAPI_MakePrism(face.wrapped,gp_Vec(0,0,dz)).Shape())

def crest(bore=4):
    px=.2
    a=np.array(Image.open(ROOT/'crest.png').convert('RGBA'))
    alpha=a[:,:,3]>100
    # Convex backing joins the spaced banners and footballs into a single keychain.
    pts=cv2.findNonZero(alpha.astype('uint8')); hull=cv2.convexHull(pts)
    backing=np.zeros(alpha.shape,np.uint8); cv2.fillConvexPoly(backing,hull,1)
    body=prism(profiles(backing,px,0,.65)[0],2.6)
    loop=cq.Workplane('XY').center(29.6,2.1).circle(4.6).extrude(2.6).val()
    body=body.fuse(loop)
    hole=cq.Workplane('XY').center(29.6,2.1).circle(bore/2).extrude(5).val()
    field=(a[:,:,0]>80)&alpha
    gold=(a[:,:,1]>112)&alpha
    # Start both bands at the backing to avoid gaps after separate simplifications.
    for mask,h in [(field,.65),(gold,1.45)]:
        smooth=cv2.resize(mask.astype('float32'),None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC)>.50
        if h==.65:
            smooth=cv2.dilate(smooth.astype('uint8'),np.ones((5,5),np.uint8))
        faces=profiles(smooth,px/3,2.6,1.15,20)
        parts=[prism(f,h) for f in faces if f.isValid()]
        body=body.fuse(*parts)
    return body.cut(hole).clean()

if __name__=='__main__':
    name=sys.argv[1]
    from terrain_mesh import terrain
    part={'crest':crest,'madeira':terrain}[name](*map(float,sys.argv[2:]))
    print('build',name,part.isValid(),len(part.Solids()),flush=True)
    cq.exporters.export(part,str(OUT/(name+'.step')))
