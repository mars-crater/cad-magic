import cadquery as cq, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os
s=cq.importers.importStep(os.path.join(os.path.dirname(__file__),'spinner.step')).val()
v,t=s.tessellate(.18,.12); v=np.array([p.toTuple() for p in v]); tris=v[np.array(t)]
n=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]); n=n/(np.linalg.norm(n,axis=1)[:,None]+1e-12); light=np.array([-.4,-.3,.86]); shade=.45+.5*np.abs(n@light)
colors=np.column_stack([shade*.82,shade*.87,shade*.92,np.ones(len(shade))]); center=tris.mean(axis=1); hub=(np.linalg.norm(center[:,:2],axis=1)<23)&(center[:,2]>5.1); colors[hub,:3]*=np.array([1.15,.76,.35]); colors=np.clip(colors,0,1)
for name,elev,az in [('top',90,-90),('oblique',32,-55)]:
 fig=plt.figure(figsize=(10,8),facecolor='white'); ax=fig.add_subplot(111,projection='3d'); ax.add_collection3d(Poly3DCollection(tris,facecolors=colors,edgecolors='none')); ax.set_xlim(-70,70); ax.set_ylim(-70,70); ax.set_zlim(-70,70); ax.set_box_aspect((1,1,1)); ax.view_init(elev,az); ax.set_axis_off(); plt.subplots_adjust(0,0,1,1); fig.savefig(os.path.join(os.path.dirname(__file__),name+'.png'),dpi=180); plt.close(fig)
