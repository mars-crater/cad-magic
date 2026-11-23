from PIL import Image,ImageDraw
import numpy as np
from scipy.ndimage import binary_fill_holes,label,map_coordinates
from scipy.interpolate import CubicSpline
im=Image.open('Banana.jpg')
a=np.asarray(im).astype(float)
r,g,b=a.transpose(2,0,1)
xx,yy=np.meshgrid(np.arange(a.shape[1]),np.arange(a.shape[0]))
shadow_line=np.interp(xx,[0,140,155,170,185,200,225,250,265,280,295,310,325,340,488],[315,315,318,322,326,330,332,332,331,329,326,323,319,315,315])
shadow=((yy>=315)&(yy>shadow_line))
labels,n=label(((r-b)>21)&((g-b)>12)&(r>35)&~shadow)
mask=binary_fill_holes(labels==np.argmax(np.bincount(labels[labels>0])))
# bincount keeps the zero index even if labels[labels>0] excludes it.
Image.fromarray(mask.astype('uint8')*255).save('reference-mask.png')
pts=np.array([(64,107),(66,121),(72,156),(77,174),(91,199),(120,232),(155,258),(198,278),(240,287),(278,285),(320,276),(363,261),(395,246),(418,235),(433.5,228)])
s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
spline=CubicSpline(s,pts)
length=s[-1]
out=Image.fromarray(np.where(mask[:,:,None],np.asarray(im),255).astype('uint8'))
d=ImageDraw.Draw(out)
print('length',length,'area',mask.sum())
for si in sorted([0,length,*np.arange(12,length-5,12)]):
    c=spline(si); t=spline(si,1); nx,ny=np.array([-t[1],t[0]])/np.linalg.norm(t)
    vals=np.arange(-65,65,.25)
    xs,ys=c[:,None]+np.array([nx,ny])[:,None]*vals
    good=map_coordinates(mask.astype(float),[ys,xs],order=1)>0.5
    if si==0:
        ends=[(77,102),(51,112)]
    elif si==length:
        ends=[(429,218),(438.5,238)]
    elif good.any():
        ends=[(xs[good][0],ys[good][0]),(xs[good][-1],ys[good][-1])]
    else: continue
    d.line(ends,fill='magenta')
    print(tuple(tuple(round(v,2) for v in e) for e in ends),',')
out.save('stations.png')
