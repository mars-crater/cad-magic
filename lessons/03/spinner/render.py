"""Render matched orthographic views from the saved STEP, not the model builder."""
from pathlib import Path
import cadquery as cq
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PAPER = "#f6f4ee"
INK = "#233949"


def unit(v):
    v = np.array(v, dtype=float)
    return v/np.linalg.norm(v)


def view(part, camera, size):
    width, height = size
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy
    from PIL import ImageColor

    scene = vtk.vtkRenderer()
    scene.SetBackground(*(v/255 for v in ImageColor.getrgb(PAPER)))
    for face in part.Faces():
        center = face.Center()
        radius = np.hypot(center.x,center.y)
        color = (144,192,202)
        if radius < 17:
            color = (87,110,126)
            if center.z > 2.41 and radius < 11.81:
                color = (240,167,80)
        elif center.z < -1.8:
            color = (113,137,153)
        vertices, triangles = face.tessellate(.035,.08)
        points = vtk.vtkPoints()
        for vertex in vertices:
            points.InsertNextPoint(*vertex.toTuple())
        cells = vtk.vtkCellArray()
        for tri in triangles:
            cells.InsertNextCell(3,tri)
        mesh = vtk.vtkPolyData()
        mesh.SetPoints(points)
        mesh.SetPolys(cells)
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(mesh)
        normals.SplittingOff()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        material = actor.GetProperty()
        material.SetColor(*(v/255 for v in color))
        material.SetAmbient(.27)
        material.SetDiffuse(.73)
        material.SetSpecular(.25)
        material.SetSpecularPower(24)
        scene.AddActor(actor)
    eye = unit(camera)
    right = unit(np.cross([0,1,0],eye))
    up = np.cross(eye,right)
    camera = scene.GetActiveCamera()
    camera.SetPosition(*(eye*230))
    camera.SetFocalPoint(0,0,0)
    camera.SetViewUp(*up)
    camera.ParallelProjectionOn()
    vertices,_ = part.tessellate(.06)
    cloud = np.array([v.toTuple() for v in vertices])
    camera.SetParallelScale(1.07*max(abs(cloud@up).max(),
                                     abs(cloud@right).max()*height/width))
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(2*width,2*height)
    window.AddRenderer(scene)
    window.Render()
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.Update()
    pixels = vtk_to_numpy(capture.GetOutput().GetPointData().GetScalars())
    image = Image.fromarray(pixels.reshape(2*height,2*width,3)[::-1])
    window.Finalize()
    return image.resize(size,Image.Resampling.LANCZOS)


if __name__ == "__main__":
    part = cq.importers.importStep(str(HERE/"spinner.step")).val()
    page = Image.new("RGB",(1320,550),PAPER)
    page.paste(view(part,[.33,-.75,.76],(785,475)),(8,43))
    page.paste(view(part,[0,0,1],(495,475)),(805,43))
    pen = ImageDraw.Draw(page)
    pen.line((799,36,799,510),fill="#c4cccb",width=1)
    for x,caption in [(35,"AIRFOIL, SPLIT TIP & OPEN NACELLE"),(830,"SIX INSTANCES  /  60° PITCH")]:
        pen.text((x,13),caption,font=ImageFont.load_default(size=19),fill=INK)
    page.save(HERE/"spinner.png")
