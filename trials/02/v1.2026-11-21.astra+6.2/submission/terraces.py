"""Contour-extruded relief, depth normalized to the reference's grayscale range."""
from build import OUT,ROOT,cv2,cq,np,Image,profiles,prism
import sys
def terrain(rise=15):
    ref=np.array(Image.open(ROOT/'inputs/madeira.png'),dtype='float32')
    smooth=cv2.resize(cv2.GaussianBlur(ref,(3,3),.65),None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC)
    n=14
    coast=max(profiles(smooth>1,.55/3,0,1.6,12),key=lambda f:f.Area())
    if not coast.isValid(): raise ValueError('invalid coastline')
    base=prism(coast,2.5)
    for k in range(1,n+1):
        z=2.5+(k-1)*rise/n
        threshold=(k-.5)*float(ref.max())/n
        fs=profiles(smooth>threshold,.55/3,z,.95,12)
        pieces=[prism(f,rise/n) for f in fs if f.isValid()]
        if pieces:
            base=base.fuse(*pieces)
    return max(base.Solids(),key=lambda s:s.Volume()).clean()
if __name__=='__main__':
    s=terrain(*map(float,sys.argv[1:]));print(s.isValid(),len(s.Solids()),flush=True)
    cq.exporters.export(s,str(OUT/'madeira-terraced.step'))
