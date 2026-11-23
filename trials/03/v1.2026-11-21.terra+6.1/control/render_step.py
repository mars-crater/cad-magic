#!/tmp/cad-magic-venv/bin/python
"""Render tessellated, reimported nominal STEP with VTK's depth buffer."""
from pathlib import Path
import cadquery as cq
import vtk
p = Path(__file__).resolve().parent
shape = cq.importers.importStep(str(p / 'dial_8.step')).val()
verts, tris = shape.tessellate(0.04, 0.08)
points = vtk.vtkPoints()
for v in verts: points.InsertNextPoint(*v.toTuple())
cells = vtk.vtkCellArray()
for t in tris:
    tri = vtk.vtkTriangle()
    for j, i in enumerate(t): tri.GetPointIds().SetId(j, i)
    cells.InsertNextCell(tri)
poly = vtk.vtkPolyData(); poly.SetPoints(points); poly.SetPolys(cells)
mapper = vtk.vtkPolyDataMapper(); mapper.SetInputData(poly)
actor = vtk.vtkActor(); actor.SetMapper(mapper)
actor.GetProperty().SetColor(0.65, 0.72, 0.79)
actor.GetProperty().SetAmbient(0.3); actor.GetProperty().SetDiffuse(0.7)
renderer = vtk.vtkRenderer(); renderer.SetBackground(0.91, 0.93, 0.95); renderer.AddActor(actor)
camera = renderer.GetActiveCamera(); camera.SetPosition(85, -110, 100); camera.SetFocalPoint(0, 0, 2); camera.SetViewUp(0, 0, 1); camera.ParallelProjectionOn(); camera.SetParallelScale(43)
window = vtk.vtkRenderWindow(); window.SetOffScreenRendering(1); window.SetSize(1400, 1000); window.AddRenderer(renderer); window.SetMultiSamples(8); window.Render()
f = vtk.vtkWindowToImageFilter(); f.SetInput(window); f.Update()
w = vtk.vtkPNGWriter(); w.SetFileName(str(p / 'dial_8.png')); w.SetInputConnection(f.GetOutputPort()); w.Write()
