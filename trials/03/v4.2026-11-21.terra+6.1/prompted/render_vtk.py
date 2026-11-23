import cadquery as cq, vtk
from pathlib import Path
p=Path(__file__).parent
s=cq.importers.importStep(str(p/'spinner.step')).val()
for name,pos,up in [('top',(0,0,300),(0,1,0)),('oblique',(150,-230,180),(0,0,1))]:
 ren=vtk.vtkRenderer(); ren.SetBackground(0.97,0.98,1)
 for part in s.Solids():
  vs,ts=part.tessellate(0.2,0.1); points=vtk.vtkPoints()
  for v in vs: points.InsertNextPoint(v.x,v.y,v.z)
  cells=vtk.vtkCellArray()
  for t in ts:
   tri=vtk.vtkTriangle()
   for i,idx in enumerate(t): tri.GetPointIds().SetId(i,idx)
   cells.InsertNextCell(tri)
  data=vtk.vtkPolyData(); data.SetPoints(points); data.SetPolys(cells)
  normals=vtk.vtkPolyDataNormals(); normals.SetInputData(data); normals.ConsistencyOn(); normals.AutoOrientNormalsOn(); normals.Update()
  m=vtk.vtkPolyDataMapper(); m.SetInputConnection(normals.GetOutputPort()); a=vtk.vtkActor(); a.SetMapper(m)
  c=part.Center(); a.GetProperty().SetColor((0.91,0.52,0.19) if c.x*c.x+c.y*c.y<340 and c.z>2.7 else (0.72,0.78,0.81)); a.GetProperty().SetSpecular(.25); a.GetProperty().SetSpecularPower(30); ren.AddActor(a)
 win=vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(1200,1000); win.AddRenderer(ren)
 cam=ren.GetActiveCamera(); cam.SetPosition(*pos); cam.SetFocalPoint(0,0,0); cam.SetViewUp(*up); cam.ParallelProjectionOn(); cam.SetParallelScale(85); ren.ResetCameraClippingRange(); win.Render()
 f=vtk.vtkWindowToImageFilter(); f.SetInput(win); f.Update(); wr=vtk.vtkPNGWriter(); wr.SetFileName(str(p/(name+'.png'))); wr.SetInputConnection(f.GetOutputPort()); wr.Write()
