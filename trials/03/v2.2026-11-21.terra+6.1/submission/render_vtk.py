import os
import vtk
import cadquery as cq
P=os.path.dirname(os.path.abspath(__file__))
s=cq.importers.importStep(os.path.join(P,'spinner.step')).val()
for name,pos in [('top',(0,0,250)),('oblique',(150,-190,130))]:
 ren=vtk.vtkRenderer(); ren.SetBackground(.94,.95,.97)
 for i,solid in enumerate(s.Solids()):
  vs,ts=solid.tessellate(.12); points=vtk.vtkPoints(); cells=vtk.vtkCellArray()
  for v in vs: points.InsertNextPoint(v.x,v.y,v.z)
  for t in ts:
   tri=vtk.vtkTriangle()
   for j in range(3): tri.GetPointIds().SetId(j,t[j])
   cells.InsertNextCell(tri)
  poly=vtk.vtkPolyData(); poly.SetPoints(points); poly.SetPolys(cells)
  normals=vtk.vtkPolyDataNormals(); normals.SetInputData(poly); normals.ConsistencyOn(); normals.AutoOrientNormalsOn(); normals.Update()
  mapper=vtk.vtkPolyDataMapper(); mapper.SetInputConnection(normals.GetOutputPort())
  actor=vtk.vtkActor(); actor.SetMapper(mapper)
  actor.GetProperty().SetColor((.88,.51,.16) if i in (2,3,4) else ((.72,.77,.82) if i>=5 else (.38,.43,.49)))
  actor.GetProperty().SetSpecular(.28); actor.GetProperty().SetSpecularPower(25); ren.AddActor(actor)
 win=vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(1200,900); win.AddRenderer(ren)
 cam=ren.GetActiveCamera(); cam.SetPosition(*pos); cam.SetFocalPoint(0,0,0); cam.SetViewUp(0,1,0) if name=='top' else cam.SetViewUp(0,0,1)
 cam.ParallelProjectionOn(); cam.SetParallelScale(97); ren.ResetCameraClippingRange(); win.Render()
 w=vtk.vtkWindowToImageFilter(); w.SetInput(win); w.Update(); out=vtk.vtkPNGWriter(); out.SetFileName(os.path.join(P,name+'.png')); out.SetInputConnection(w.GetOutputPort()); out.Write(); win.Finalize()
