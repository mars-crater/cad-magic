"""Single unpainted material, orthographic views of STEP meshes using a depth buffer."""
from pathlib import Path
import sys,cadquery as cq,vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray
import numpy as np
out=Path(__file__).resolve().parent
stem=sys.argv[1]
s=cq.importers.importStep(str(out/(stem+'.step'))).val()
v,f=s.tessellate(.025,.12)
pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.array([p.toTuple() for p in v])))
cells=vtk.vtkCellArray();cells.SetCells(len(f),numpy_to_vtkIdTypeArray(np.column_stack((np.full(len(f),3),f)).astype('int64').ravel(),deep=True))
mesh=vtk.vtkPolyData();mesh.SetPoints(pts);mesh.SetPolys(cells)
mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(mesh)
actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(.78,.78,.78)
r=vtk.vtkRenderer();r.AddActor(actor);r.SetBackground(.98,.98,.98);r.SetUseSSAO(True);r.SetSSAORadius(2.5);r.SetSSAOBias(.025);r.SetSSAOKernelSize(128)
w=vtk.vtkRenderWindow();w.SetOffScreenRendering(1);w.SetSize(800,800);w.SetMultiSamples(0);w.AddRenderer(r)
c=r.GetActiveCamera()
for name,pos in [('top',(0,0,100)),('oblique',(50,-75,85))]:
    c.SetPosition(*pos);c.SetFocalPoint(0,0,0);c.SetViewUp(0,1,0) if name=='top' else c.SetViewUp(0,0,1)
    c.ParallelProjectionOn();r.ResetCamera()
    if name=='top':c.SetParallelScale(42 if stem=='final' else 7.2)
    w.Render();flt=vtk.vtkWindowToImageFilter();flt.SetInput(w);flt.Update()
    png=vtk.vtkPNGWriter();png.SetFileName(str(out/(stem+'-'+name+'.png')));png.SetInputConnection(flt.GetOutputPort());png.Write()
