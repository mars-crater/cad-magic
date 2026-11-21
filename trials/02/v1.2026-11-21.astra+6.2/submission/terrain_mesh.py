"""Heightfield alternative: triangulated terrain clipped to the main-island mask."""
from build import OUT, ROOT, cq, cv2, np, Image
from scipy.spatial import Delaunay
from collections import Counter
import sys

def terrain(height=15):
    data=np.array(Image.open(ROOT/'inputs/madeira.png'),float)
    coast=max(cv2.findContours((data>1).astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0],key=cv2.contourArea)
    outline=cv2.approxPolyDP(coast,.65,True)[:,0]
    points=[tuple(p) for p in outline]
    for y in range(0,data.shape[0],3):
        for x in range(0,data.shape[1],3):
            if cv2.pointPolygonTest(coast,(x,y),True)>1.4: points.append((x,y))
    points=np.unique(points,axis=0)
    mesh=Delaunay(points)
    smooth=cv2.GaussianBlur(data,(5,5),.85)
    top=[cq.Vector(x*.55,-y*.55,2.5+height*smooth[y,x]/data.max()) for x,y in points]
    bot=[cq.Vector(p.x,p.y,0) for p in top]
    def face(ps):
        return cq.Face.makeFromWires(cq.Wire.makePolygon(ps,close=True))
    faces=[]; edge_counts=Counter()
    from collections import defaultdict
    kept={i for i,t in enumerate(mesh.simplices)
          if cv2.pointPolygonTest(coast,tuple(points[t].mean(axis=0)),False)>=0}
    # A silhouette can touch at one vertex in a pixelated cove. Join fans at
    # such junctions before extrusion, avoiding a non-manifold vertical edge.
    for _ in range(15):
        edges=Counter(tuple(sorted((a,b))) for i in kept for a,b in
                      zip(mesh.simplices[i],np.roll(mesh.simplices[i],-1)))
        deg=Counter(p for e,n in edges.items() if n==1 for p in e)
        pinches={p for p,n in deg.items() if n>2}
        if not pinches: break
        kept.update(i for i,t in enumerate(mesh.simplices) if pinches.intersection(t))
    for index in sorted(kept):
        tri=mesh.simplices[index]
        a,b,c=tri # planar coordinates flipped in y; reverse top orientation
        faces.extend([face([top[c],top[b],top[a]]),face([bot[a],bot[b],bot[c]])])
        for i,j in [(a,b),(b,c),(c,a)]:edge_counts[(i,j)]+=1
    for i,j in edge_counts:
        if (j,i) not in edge_counts: faces.append(face([top[i],top[j],bot[j],bot[i]]))
    return cq.Solid.makeSolid(cq.Shell.makeShell(faces)).clean()
if __name__=='__main__':
    part=terrain(*map(float,sys.argv[1:]));print(part.isValid(),len(part.Solids()),flush=True)
    cq.exporters.export(part,str(OUT/'madeira.step'))
