import cadquery as cq, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path
p=Path(__file__).parent

def read(name): return cq.importers.importStep(str(p/name)).val()
def render(shape,name,elev,azim):
 fig=plt.figure(figsize=(10,8)); ax=fig.add_subplot(projection='3d')
 for s in shape.Solids():
  verts,tris=s.tessellate(0.35,0.15); pts=np.array([[v.x,v.y,v.z] for v in verts]); faces=pts[np.array(tris)]
  c=s.Center(); color='#dd943c' if (c.x*c.x+c.y*c.y<330 and c.z>2.7) else '#b8c5cc'
  ax.add_collection3d(Poly3DCollection(faces,facecolors=color,edgecolor='none',alpha=1,shade=True,lightsource=matplotlib.colors.LightSource(azdeg=315,altdeg=45)))
 ax.set(xlim=(-78,78),ylim=(-78,78),zlim=(-20,20)); ax.set_box_aspect((156,156,40)); ax.view_init(elev,azim); ax.axis('off'); fig.tight_layout(); fig.savefig(p/name,dpi=180); plt.close(fig)
seed=read('seed.step'); model=read('spinner.step')
render(seed,'seed_top.png',90,-90); render(seed,'seed_section.png',0,-90)
render(model,'top.png',90,-90); render(model,'oblique.png',30,-65)
for name,s in [('seed',seed),('spinner',model)]:
 b=s.BoundingBox(); print(name,'solids',len(s.Solids()),'valid',s.isValid(),'bbox mm',*(round(v,3) for v in (b.xlen,b.ylen,b.zlen)),'volume',round(s.Volume(),3))
print('seed section stations: x, width, center z, thickness')
for x,w,z in [(19,15,0),(34,17,.2),(49,18,.8),(63,19,2.2),(71,19,5.2)]: print(x,w,z,2.6)
