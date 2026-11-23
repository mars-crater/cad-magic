#!/usr/bin/env python3
import os, math, json
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from spinner import build
P=os.path.dirname(os.path.abspath(__file__))
s=cq.importers.importStep(os.path.join(P,'spinner.step')).val()
solids=s.Solids(); bb=s.BoundingBox()
report={'reimport_valid':s.isValid(),'solid_count':len(solids),'bbox_mm':[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax], 'volume_mm3':sum(x.Volume() for x in solids)}
# Verify exact patterned wing solids by indexed export structure and radial centroids.
wing_centres=[]
for i in range(6):
 c=solids[5+4*i].Center(); wing_centres.append([round(c.x,3),round(c.y,3)])
report['wing_centroids_xy_mm']=wing_centres
report['wing_centroid_radii_mm']=[round(math.hypot(*xy),3) for xy in wing_centres]
print(json.dumps(report,indent=2))
with open(os.path.join(P,'verification.json'),'w') as f: json.dump(report,f,indent=2)
