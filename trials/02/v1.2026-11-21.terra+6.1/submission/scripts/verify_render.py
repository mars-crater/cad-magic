import cadquery as cq, json, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path
P=Path(__file__).resolve().parents[1]
report={}
for name in ('madeira','crest'):
    obj=cq.importers.importStep(str(P/'results'/f'{name}.step')).val(); b=obj.BoundingBox(); solids=obj.Solids()
    report[name]={'valid':obj.isValid(),'solids':len(solids),'bbox_mm':[b.xlen,b.ylen,b.zlen],'volume_sum_mm3':sum(s.Volume() for s in solids)}
    if name=='crest':
        probe=cq.Solid.makeCylinder(2.9,4,cq.Vector(0,34,-1)); report[name]['bore_probe_intersection_mm3']=sum(s.intersect(probe).Volume() for s in solids)
    mesh=[]
    for s in solids:
        v,t=s.tessellate(.3,.2)
        mesh += [[[v[j].x,v[j].y,v[j].z] for j in tri] for tri in t]
    for view,elev,azim in [('top',90,-90),('oblique',28,-60)]:
        fig=plt.figure(figsize=(10,7)); ax=fig.add_subplot(111,projection='3d'); poly=Poly3DCollection(mesh,facecolors='#c4ab80',shade=True,lightsource=matplotlib.colors.LightSource(azdeg=315,altdeg=50)); ax.add_collection3d(poly)
        ax.set_xlim(b.xmin,b.xmax);ax.set_ylim(b.ymin,b.ymax);ax.set_zlim(0,max(b.zmax,1)); ax.set_box_aspect((b.xlen,b.ylen,b.zlen));ax.view_init(elev,azim);ax.set_axis_off();fig.savefig(P/'renders'/f'{name}-{view}.png',dpi=180,bbox_inches='tight',pad_inches=.02);plt.close(fig)
    print(name,report[name],flush=True)
(P/'results'/'verification.json').write_text(json.dumps(report,indent=2))
