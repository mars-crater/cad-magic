"""Fresh STEP reader; neutral-material camera views and section comparisons."""
from pathlib import Path
import sys,json
import numpy as np
import cv2
import cadquery as cq
import vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray
from PIL import Image
P=Path(__file__).resolve().parent
name=sys.argv[1]
s=cq.importers.importStep(str(P/(name+'.step'))).val()
b=s.BoundingBox()
v,t=s.tessellate(.045,.12)
xyz=np.array([p.toTuple() for p in v]);tri=np.array(t,dtype=np.int64)
pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(xyz,deep=True))
cells=vtk.vtkCellArray();cells.SetData(numpy_to_vtkIdTypeArray(np.arange(0,3*len(tri)+1,3,dtype=np.int64)),numpy_to_vtkIdTypeArray(tri.ravel()))
poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(poly)
actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(.84,.81,.73)
ren=vtk.vtkRenderer(); ren.AddActor(actor);ren.SetBackground(.12,.14,.16)
win=vtk.vtkRenderWindow();win.SetOffScreenRendering(True);win.SetSize(900,760);win.AddRenderer(ren)
c=np.array([(b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2,(b.zmin+b.zmax)/2])
light=vtk.vtkLight(); light.SetPosition(*(c+[-95,65,110]));light.SetFocalPoint(*c);ren.AddLight(light)
actor.GetProperty().SetAmbient(.26);actor.GetProperty().SetDiffuse(.8)
for view,offset in [('top',[0,0,200]),('oblique',[55,-145,130])]:
    cam=ren.GetActiveCamera();cam.SetPosition(*(c+offset));cam.SetFocalPoint(*c);cam.SetViewUp(0,1,0);cam.ParallelProjectionOn()
    cam.SetParallelScale(max(b.ylen,b.xlen*760/900)*.56);ren.ResetCameraClippingRange();win.Render()
    grab=vtk.vtkWindowToImageFilter();grab.SetInput(win);grab.Update()
    from vtk.util.numpy_support import vtk_to_numpy
    from scipy.ndimage import shift
    colors=vtk_to_numpy(grab.GetOutput().GetPointData().GetScalars()).reshape(760,900,3)[::-1].copy()
    depthgrab=vtk.vtkWindowToImageFilter();depthgrab.SetInput(win);depthgrab.SetInputBufferTypeToZBuffer();depthgrab.Update()
    depth=vtk_to_numpy(depthgrab.GetOutput().GetPointData().GetScalars()).reshape(760,900)[::-1].copy()
    near,far=cam.GetClippingRange()
    depth_mm=near+depth*(far-near)
    pitch=2*cam.GetParallelScale()/760
    shade=np.zeros(depth.shape)
    # Orthographic depth-based contact shadows for light from upper left.
    for step in range(1,27):
        neighbor=shift(depth_mm,(step,step),order=0,mode='nearest')
        occlusion=np.clip((depth_mm-neighbor-step*pitch*.62)/.42,0,1)
        shade=np.maximum(shade,occlusion*np.exp(-step/20))
    shade[depth>=.99999]=0
    Image.fromarray((colors*(1-.58*shade[:,:,None])).astype('uint8')).save(P/f'{name}-{view}.png')

def section_iou(z,scale,target):
    # Project above-plane portions of the reimported triangle mesh, including
    # partially clipped triangles, into source pixel coordinates.
    plane=vtk.vtkPlane();plane.SetOrigin(0,0,z);plane.SetNormal(0,0,1)
    clip=vtk.vtkClipPolyData();clip.SetInputData(poly);clip.SetClipFunction(plane);clip.Update()
    from vtk.util.numpy_support import vtk_to_numpy
    cut=clip.GetOutput(); pixels=vtk_to_numpy(cut.GetPoints().GetData())[:,:2]/[scale,-scale]
    raster=np.zeros(target.shape,np.uint8)
    for i in range(cut.GetNumberOfCells()):
        cell=cut.GetCell(i)
        coords=np.rint([pixels[cell.GetPointId(k)] for k in range(cell.GetNumberOfPoints())]).astype('int32')
        cv2.fillConvexPoly(raster,coords,1)
    return round(np.logical_and(raster,target).sum()/np.logical_or(raster,target).sum(),4)
report={'valid':s.isValid(),'solids':len(s.Solids()),'mm':[round(k,3) for k in (b.xlen,b.ylen,b.zlen)],'faces':len(s.Faces())}
if name=='madeira':
    ref=np.array(Image.open(P.parent/'inputs/madeira.png'))
    report['section_IoU']={str(h):section_iou(2.5+15*float(h)/ref.max(),.55,ref>h) for h in (2,60,120,180)}
else:
    ref=np.array(Image.open(P.parent/'crest.png').convert('RGBA'));alpha=ref[:,:,3]>100
    report['section_IoU']={'field':section_iou(2.95,.2,(ref[:,:,0]>80)&alpha),'gold':section_iou(3.75,.2,(ref[:,:,1]>112)&alpha)}
    report['bore_void_at_z']={str(z):not s.isInside((29.6,2.1,z)) for z in (.1,1.3,2.5)}
    report['rim_material']=s.isInside((32.7,2.1,1.3))
    report['cylinder_diameters_mm']=[round(2*f._geomAdaptor().Cylinder().Radius(),4) for f in s.Faces() if f.geomType()=='CYLINDER']
(P/f'{name}-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
