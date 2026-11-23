"""Rebuild with the supplied Python environment. Units: mm."""
from pathlib import Path
import io
import json
import cadquery as cq
import cairosvg
import cv2
import numpy as np
from PIL import Image
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray

OUT = Path(__file__).resolve().parent
WIDTH, BASE, BORE = 60., 2.8, 4.4
PX = 6
image = np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(
    url=str(OUT/'reference.svg'), output_width=160*PX, output_height=180*PX))).convert('RGB')).astype(float)
palette = np.array([[255,255,255], [39,57,71], [152,100,56]])
labels = np.argmin(((image[:,:,None,:]-palette)**2).sum(axis=3),axis=2)
S = WIDTH/146
def xy(x,y):
    return ((x-80)*S,(84-y)*S)

def feature(label,height):
    contours, tree = cv2.findContours((labels==label).astype('uint8'),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    wires = []
    for c in contours:
        points = cv2.approxPolyDP(c,1.15,True).reshape(-1,2)
        if len(points)<3 or cv2.contourArea(c)<8:
            wires.append(None)
            continue
        vertices = [cq.Vector(*xy((x+.5)/PX,(y+.5)/PX),BASE) for x,y in points]
        wires.append(cq.Wire.makePolygon(vertices,close=True))
    solids=[]
    for i, w in enumerate(wires):
        if w is None or tree[0,i,3] != -1: continue
        holes=[h for j,h in enumerate(wires) if h is not None and tree[0,j,3]==i]
        solids.append(cq.Solid.extrudeLinear(w,holes,(0,0,height)))
    return solids

def build(bore):
    body = cq.Workplane('XY').box(WIDTH,166*S,BASE,centered=(True,True,False)).edges('|Z').fillet(8).val()
    for solid in feature(1,1.)+feature(2,1.6):
        body=body.fuse(solid)
    return body.cut(cq.Solid.makeCylinder(bore/2,8,cq.Vector(*xy(80,24),-1))).clean()

def render(shape, name, direction):
    vs,fs=shape.tessellate(.035,.12)
    points=vtk.vtkPoints()
    points.SetData(numpy_to_vtk(np.array([v.toTuple() for v in vs])))
    cells=vtk.vtkCellArray()
    cells.SetCells(len(fs),numpy_to_vtkIdTypeArray(np.column_stack((np.full(len(fs),3),fs)).astype('int64').ravel(),deep=True))
    mesh=vtk.vtkPolyData(); mesh.SetPoints(points); mesh.SetPolys(cells)
    mapper=vtk.vtkPolyDataMapper(); mapper.SetInputData(mesh)
    actor=vtk.vtkActor(); actor.SetMapper(mapper); actor.GetProperty().SetColor(.85,.77,.60)
    scene=vtk.vtkRenderer(); scene.AddActor(actor); scene.SetBackground(.18,.20,.23)
    clean=vtk.vtkCleanPolyData();clean.SetInputData(mesh)
    edges=vtk.vtkFeatureEdges();edges.SetInputConnection(clean.GetOutputPort());edges.SetFeatureAngle(56);edges.BoundaryEdgesOff();edges.ManifoldEdgesOff();edges.NonManifoldEdgesOff()
    lines=vtk.vtkPolyDataMapper();lines.SetInputConnection(edges.GetOutputPort());lines.ScalarVisibilityOff();lines.SetResolveCoincidentTopologyToPolygonOffset();lines.SetRelativeCoincidentTopologyLineOffsetParameters(0,-3)
    ink=vtk.vtkActor();ink.SetMapper(lines);ink.GetProperty().SetColor(.26,.22,.18);ink.GetProperty().SetLineWidth(1.6);scene.AddActor(ink)
    cam=scene.GetActiveCamera(); cam.SetPosition(*direction); cam.SetFocalPoint(0,0,2);cam.SetViewUp(0,1,0);cam.ParallelProjectionOn();cam.SetParallelScale(41)
    light=vtk.vtkLight();light.SetPosition(-60,40,60);light.SetFocalPoint(0,0,0);light.SetIntensity(.95);scene.AddLight(light)
    actor.GetProperty().SetAmbient(.32)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(740,800);win.AddRenderer(scene);win.Render()
    grab=vtk.vtkWindowToImageFilter();grab.SetInput(win);grab.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(OUT/name));writer.SetInputConnection(grab.GetOutputPort());writer.Write();win.Finalize()

def section_mask(part,z):
    mask=np.zeros(labels.shape,np.uint8)
    for face in cq.Workplane(obj=part).section(z).val().Faces():
        for w,col in [(face.outerWire(),1)]+[(w,0) for w in face.innerWires()]:
            pts=w.sample(.015)[0]
            poly=np.array([[(p.x/S+80)*PX-.5,(84-p.y/S)*PX-.5] for p in pts])
            cv2.fillPoly(mask,[poly.round().astype('int32')],col)
    return mask.astype(bool)

if __name__=='__main__':
    part=build(BORE);cq.exporters.export(part,str(OUT/'final.step'))
    saved=cq.importers.importStep(str(OUT/'final.step')).val()
    bb=saved.BoundingBox()
    data={'solid_count':len(saved.Solids()),'valid':saved.isValid(),'dimensions_mm':[bb.xlen,bb.ylen,bb.zlen]}
    for z,ref in [(3.3,labels!=0),(4.1,labels==2)]:
        actual=section_mask(saved,z)
        data[f'section_{z}_source_IoU']=np.sum(actual & ref)/np.sum(actual | ref)
    def bore_check(shape):
        return [(e.radius()*2,e.arcCenter().toTuple()) for e in shape.Edges() if e.geomType()=='CIRCLE' and abs(e.arcCenter().y-xy(80,24)[1])<.001 and abs(e.arcCenter().x)<.001]
    data['bore_rims_diameter_center_mm']=bore_check(saved)
    probe=cq.Solid.makeCylinder(BORE/2-.001,10,cq.Vector(*xy(80,24),-2))
    data['through_probe_4.398mm_intersection_mm3']=saved.intersect(probe).Volume()
    alt=build(5.0)
    data['5mm_bore_rebuild']={'valid':alt.isValid(),'rims':bore_check(alt),'width':alt.BoundingBox().xlen}
    (OUT/'checks.json').write_text(json.dumps(data,indent=2)+'\n')
    render(saved,'top.png',(0,0,100));render(saved,'oblique.png',(55,-80,105))
