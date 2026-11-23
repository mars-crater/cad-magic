import cadquery as cq
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path
P=Path(__file__).resolve().parent
shape=cq.importers.importStep(str(P/'wing.step')).val()
solids=shape.Solids(); b=shape.BoundingBox()
print('solids',len(solids),'valid',all(s.isValid() for s in solids),'bbox',*(round(v,3) for v in (b.xlen,b.ylen,b.zlen)),'volume',round(sum(s.Volume() for s in solids),3))
polys=[]
for s in solids:
    v,t=s.tessellate(0.5,0.12)
    a=np.array([[p.x,p.y,p.z] for p in v])
    polys.extend(a[np.array(t)].tolist())
for name,elev,azim in [('oblique',28,-55),('top',90,-90)]:
    fig=plt.figure(figsize=(9,7),facecolor='white'); ax=fig.add_subplot(111,projection='3d')
    col=Poly3DCollection(polys,facecolors='#d5dbe1',linewidth=0,shade=True,lightsource=matplotlib.colors.LightSource(azdeg=315,altdeg=45))
    ax.add_collection3d(col); ax.set_xlim(-10,195); ax.set_ylim(-48,90); ax.set_zlim(-65,45); ax.set_box_aspect((205,138,110)); ax.view_init(elev=elev,azim=azim); ax.set_axis_off(); plt.tight_layout(); fig.savefig(P/(name+'.png'),dpi=180,bbox_inches='tight',pad_inches=.05); plt.close(fig)
