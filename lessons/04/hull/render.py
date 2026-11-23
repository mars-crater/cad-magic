"""Render the imported STEP and a half-hull cut at its longitudinal centerline."""
from pathlib import Path

import cadquery as cq
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import vtk
from vtk.util.numpy_support import vtk_to_numpy

HERE = Path(__file__).resolve().parent
PAPER = (243, 246, 245)
INK = "#1d343e"
TEAL = (47, 115, 123)
LINING = (219, 172, 113)
RIM = (190, 132, 79)
CUT = (235, 188, 106)


def unit(vector):
    vector = np.array(vector, dtype=float)
    return vector / np.linalg.norm(vector)


def add_face(scene, face, color):
    vertices, triangles = face.tessellate(.09, .10)
    points = vtk.vtkPoints()
    for point in vertices:
        points.InsertNextPoint(*point.toTuple())
    cells = vtk.vtkCellArray()
    for triangle in triangles:
        cells.InsertNextCell(3, triangle)
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
    material.SetColor(*(v / 255 for v in color))
    material.SetAmbient(.30)
    material.SetDiffuse(.68)
    material.SetSpecular(.20)
    material.SetSpecularPower(28)
    scene.AddActor(actor)


def scene_view(part, facing, size, cut=None):
    scene = vtk.vtkRenderer()
    scene.SetBackground(*(v / 255 for v in PAPER))
    for face in part.Faces():
        center = face.Center()
        box = face.BoundingBox()
        if cut is not None and abs(center.y - cut) < 1e-5 and box.ylen < 1e-5:
            color = CUT
        elif face.geomType() == "EXTRUSION":
            color = RIM
        elif face.geomType() == "PLANE":
            color = LINING if center.z > .5 else TEAL
        else:
            normals = face.normalAt(center)
            # The inside faces point into the void; the outside faces point away.
            if abs(center.y) > 1:
                inward = normals.y * center.y < 0
            else:
                inward = normals.x > 0
            color = LINING if inward else TEAL
        add_face(scene, face, color)
    eye = unit(facing)
    up_ref = [0, 1, 0] if abs(eye[2]) > .99 else [0, 0, 1]
    right = unit(np.cross(up_ref, eye))
    up = np.cross(eye, right)
    vertices, _ = part.tessellate(.15, .10)
    cloud = np.array([point.toTuple() for point in vertices])
    span_x, span_y = cloud @ right, cloud @ up
    focus = (span_x.min() + span_x.max()) / 2 * right + (span_y.min() + span_y.max()) / 2 * up
    camera = scene.GetActiveCamera()
    camera.SetPosition(*(focus + 650 * eye))
    camera.SetFocalPoint(*focus)
    camera.SetViewUp(*up)
    camera.ParallelProjectionOn()
    width, height = size
    camera.SetParallelScale(.55 * max(np.ptp(span_y), np.ptp(span_x) * height / width))
    scene.ResetCameraClippingRange()
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetMultiSamples(0)
    window.SetSize(width * 2, height * 2)
    window.AddRenderer(scene)
    window.Render()
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.Update()
    pixels = vtk_to_numpy(capture.GetOutput().GetPointData().GetScalars())
    image = Image.fromarray(pixels.reshape(2 * height, 2 * width, 3)[::-1])
    window.Finalize()
    return image.resize(size, Image.Resampling.LANCZOS)


if __name__ == "__main__":
    part = cq.importers.importStep(str(HERE / "boat-hull.step")).val()
    scene_view(part, [.18, -.89, .42], (1800, 900)).save(HERE / "boat-hull.png")
    scene_view(part, [.38, .91, .16], (1800, 690)).save(HERE / "boat-hull-profile.png")
    cutter = cq.Solid.makeBox(400, 120, 120, cq.Vector(-25, -120, -10))
    half = part.cut(cutter)
    assert half.isValid() and len(half.Solids()) == 1
    assert abs(half.Volume() / part.Volume() - .5) < .001
    page = Image.new("RGB", (1800, 1180), PAPER)
    page.paste(scene_view(half, [.14, -.94, .30], (1740, 520)), (30, 55))
    page.paste(scene_view(part, [0, 0, 1], (1740, 490)), (30, 640))
    pen = ImageDraw.Draw(page)
    font = ImageFont.load_default(size=24)
    pen.text((80, 40), "LONGITUDINAL CENTERLINE CUT", fill=INK, font=font)
    pen.line((80, 585, 1720, 585), fill="#c5d3d2", width=2)
    pen.text((80, 610), "OPEN HULL FROM ABOVE", fill=INK, font=font)
    page.save(HERE / "boat-hull-section.png")
