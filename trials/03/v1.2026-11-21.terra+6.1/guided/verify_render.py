#!/usr/bin/env python3
import math
from pathlib import Path
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.colors import LightSource
import numpy as np

root = Path(__file__).resolve().parent
for n in (8, 11):
    shape = cq.importers.importStep(str(root / f'dial-{n}.step')).val()
    bb = shape.BoundingBox()
    expected = math.pi*32**2*6 - math.pi*4**2*6 - n*(7*3+math.pi*1.5**2)*2
    assert shape.isValid() and len(shape.Solids()) == 1
    assert all(abs(a-b)<1e-6 for a,b in zip((bb.xlen,bb.ylen,bb.zlen),(64,64,6)))
    assert abs(shape.Volume()-expected)<1e-5
    assert not shape.isInside(cq.Vector(0,0,3))
    for i in range(n):
        a = 2*math.pi*i/n
        def point(r, t, z):
            return cq.Vector(r*math.cos(a)-t*math.sin(a),r*math.sin(a)+t*math.cos(a),z)
        assert not shape.isInside(point(23,0,5))
        assert shape.isInside(point(23,0,3.9))
        assert shape.isInside(point(23,1.51,5))
        assert shape.isInside(point(28.01,0,5))
        assert shape.isInside(point(17.99,0,5))
        mid = a + math.pi/n
        assert shape.isInside(cq.Vector(23*math.cos(mid),23*math.sin(mid),5))
    print(f'{n}: valid={shape.isValid()} solids={len(shape.Solids())} bbox={bb.xlen:.6f} x {bb.ylen:.6f} x {bb.zlen:.6f} mm volume={shape.Volume():.6f} mm^3 expected={expected:.6f}; sampled slots, floors, edges, gaps and bore OK; pitch={360/n:.9f} degrees')
    if n == 8:
        vertices, faces = shape.tessellate(0.08, 0.1)
        verts = np.array([(v.x,v.y,v.z) for v in vertices])
        tris = verts[np.array(faces)]
        normal = np.cross(tris[:,1]-tris[:,0], tris[:,2]-tris[:,0])
        lengths = np.linalg.norm(normal,axis=1)
        normal /= np.maximum(lengths[:,None],1e-15)
        light = np.array([-0.45,-0.55,0.70]); light /= np.linalg.norm(light)
        intensity = 0.45 + 0.48*np.abs(normal @ light)
        colors = np.array([0.40,0.57,0.70])[None,:]*intensity[:,None]+0.10
        fig = plt.figure(figsize=(8,8), facecolor='#f4f6f8')
        ax = fig.add_subplot(111, projection='3d', facecolor='#f4f6f8')
        ax.add_collection3d(Poly3DCollection(tris, facecolors=colors, edgecolors='none'))
        ax.set(xlim=(-34,34),ylim=(-34,34),zlim=(-18,30))
        ax.set_box_aspect((68,68,48)); ax.view_init(elev=34, azim=-58)
        ax.set_axis_off(); fig.tight_layout(pad=0)
        fig.savefig(root/'dial-8.png',dpi=180,facecolor=fig.get_facecolor())
