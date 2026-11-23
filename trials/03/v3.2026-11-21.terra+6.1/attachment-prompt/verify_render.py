import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path
p=Path(__file__).resolve().parent
shape=cq.importers.importStep(str(p/'wing.step')).val()
solids=shape.Solids()
print('solids',len(solids),'valid',all(s.isValid() for s in solids))
for i,s in enumerate(solids):
 b=s.BoundingBox(); print(i,'volume',round(s.Volume(),2),'bounds',*(round(v,2) for v in (b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax)))
for name,elev,azim in [('oblique',28,-58),('top',90,-90)]:
 fig=plt.figure(figsize=(10,7),facecolor='white'); ax=fig.add_subplot(projection='3d'); ax.set_proj_type('ortho')
 for i,s in enumerate(solids):
  verts,tri=s.tessellate(.18,.12); vs=[v.toTuple() for v in verts]; polys=[[vs[j] for j in t] for t in tri]
  coll=Poly3DCollection(polys,facecolors=['#d7dce3','#b4bbc5','#a6b0bc','#596472'][i],edgecolor='none',shade=True,lightsource=matplotlib.colors.LightSource(azdeg=300,altdeg=45)); ax.add_collection3d(coll)
  for edge in s.Edges():
   pts=[edge.positionAt(j/40).toTuple() for j in range(41)]; ax.plot(*zip(*pts),color='#414a55',linewidth=.45)
 ax.set_xlim(-5,120);ax.set_ylim(-65,30);ax.set_zlim(-35,35); ax.set_box_aspect((125,95,70));ax.view_init(elev,azim);ax.axis('off');fig.subplots_adjust(0,0,1,1);fig.savefig(p/(name+'.png'),dpi=180);plt.close(fig)
