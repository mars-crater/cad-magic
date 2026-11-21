import cadquery as cq, cv2, numpy as np, cairosvg, os, json
from PIL import Image
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'submission'; os.chdir(ROOT)

def contours(mask, scale, z, h, minarea=2, eps=.6):
    cs,hier=cv2.findContours(mask.astype('uint8'),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    if hier is None:return []
    H,W=mask.shape; result=[]
    def wire(c):
        p=cv2.approxPolyDP(c,eps,True)[:,0,:]
        if len(p)<3:return None
        pts=[cq.Vector((x-W/2)*scale,(H/2-y)*scale,z) for x,y in p]; pts.append(pts[0]); return cq.Wire.makePolygon(pts)
    for i,c in enumerate(cs):
        if hier[0,i,3]!=-1 or cv2.contourArea(c)<minarea:continue
        try:
            outer=wire(c)
            if outer is None:continue
            holes=[]; child=hier[0,i,2]
            while child!=-1:
                if cv2.contourArea(cs[child])>=minarea:
                    w=wire(cs[child]);
                    if w: holes.append(w)
                child=hier[0,child,0]
            result.append(cq.Solid.extrudeLinear(outer,holes,cq.Vector(0,0,h)))
        except Exception as e: print('SKIP',i,str(e)[:100],flush=True)
    return result

# Island image crops represent relative luminance, not a DEM in metres.
a=np.asarray(Image.open('inputs/madeira.png').convert('L')); a=cv2.GaussianBlur(a,(3,3),0)
# Flat sea plate: image footprint 120 mm across; land terraces are above it.
scale=120/a.shape[1]; base=cq.Workplane('XY').box(120,a.shape[0]*scale,2,centered=(True,True,False)).val(); solids=[base]
for level in (8,32,56,80,104,128,152,176,200):
    ss=contours(a>=level,scale,2+(level!=8)*0,0.65,minarea=8,eps=.75)
    # stacked independently from the base to their correct top height
    height=0.65*((level-8)//24+1)
    ss=contours(a>=level,scale,2,height,minarea=8,eps=.75)
    solids.extend(ss); print('terrain',level,len(ss),flush=True)
terrain=cq.Compound.makeCompound(solids); cq.exporters.export(terrain,str(OUT/'results/madeira.step'))
# Crest on circular backing. Colors become heights, not paint.
cairosvg.svg2png(url='inputs/cad-magic-mufc.svg',write_to=str(OUT/'results/reference-raster.png'),output_width=296,output_height=300)
im=np.asarray(Image.open(OUT/'results/reference-raster.png').convert('RGBA')); rgb=im[:,:,:3]; alpha=im[:,:,3];
# Red field raised 0.35; yellow marks raised 0.8, creating a legible two-height engraving.
red=(alpha>120)&(rgb[:,:,0]>80)&(rgb[:,:,0]>rgb[:,:,1]*1.35)&(rgb[:,:,1]<145)
yellow=(alpha>120)&(rgb[:,:,0]>140)&(rgb[:,:,1]>90)&(rgb[:,:,2]<120)&(rgb[:,:,0]>rgb[:,:,2]*1.5)
base=cq.Workplane('XY').circle(30).extrude(2).val(); ring=cq.Workplane('XY').center(0,34).circle(6).circle(3).extrude(2).val(); parts=[base,ring]
for name,mask,height in [('red',red,.35),('yellow',yellow,.8)]:
    ss=contours(mask,55/300,2,height,minarea=2,eps=.45); parts.extend(ss); print(name,len(ss),flush=True)
crest=cq.Compound.makeCompound(parts); cq.exporters.export(crest,str(OUT/'results/crest.step'))
print('EXPORTED',flush=True)
