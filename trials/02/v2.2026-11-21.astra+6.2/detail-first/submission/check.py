"""Reconstruct independent masks from horizontal STEP sections and compare with SVG ink."""
from pathlib import Path
from io import BytesIO
import cadquery as cq, cv2, numpy as np, cairosvg
from PIL import Image
out=Path(__file__).resolve().parent
s=cq.importers.importStep(str(out/'final.step')).val()
source=np.array(Image.open(BytesIO(cairosvg.svg2png(url=str(out/'reference.svg'),output_width=960,output_height=1080))).convert('RGB')).astype(float)
colors=np.array([[255,255,255],[39,57,71],[152,100,56]])
lab=((source[:,:,None]-colors)**2).sum(axis=3).argmin(axis=2)
for z,ref in [(2.8,lab!=0),(3.55,lab==2)]:
    sec=cq.Workplane(obj=s).section(z).val()
    cs=[]
    for w in sec.Wires():
        pts=w.sample(.02)[0]
        cs.append(np.array([[round(480+p.x*6/.44),round(540-p.y*6/.44)] for p in pts],np.int32))
    mask=cv2.fillPoly(np.zeros(ref.shape,'uint8'),cs,1).astype(bool)
    print(z,'section/source IoU',np.sum(mask&ref)/np.sum(mask|ref))
