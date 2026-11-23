"""Render the reopened Session 4 example STEP files beside course references."""
from math import hypot
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

import cadquery as cq
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import vtk
from vtk.util.numpy_support import vtk_to_numpy

from hull.render import INK, PAPER, add_face, unit

HERE = Path(__file__).resolve().parent
COURSE = (
    "https://raw.githubusercontent.com/andyeske/How-to-CAD-Almost-Anything/"
    "main/Session%20Files/Session%204/"
)


def tower_color(face):
    center = face.Center()
    box = face.BoundingBox()
    z = center.z
    if z < 3.1 and max(box.xlen, box.ylen) > 100:
        return (54, 118, 73)
    if face.geomType() == "PLANE" and box.zlen < .001:
        return (167, 171, 172) if z > 3 else (54, 118, 73)
    if box.zmin > 165.5 and box.zmax <= 187.1 and box.zlen > 2.2:
        return (63, 83, 150)
    if 145.9 <= box.zmin and box.zmax < 164 and box.zlen > 2.2:
        return (98, 116, 167)
    if face.geomType() == "BSPLINE":
        return (148, 152, 157)
    if hypot(center.x, center.y) < 8.1 and 15 < z < 145:
        return (83, 101, 144)
    return (150, 157, 158)


def banana_color(face):
    if face.geomType() == "PLANE":
        return (94, 55, 21)
    if face.Center().x < 14:
        return (158, 178, 56)
    if face.Center().x > 169:
        return (119, 72, 31)
    return (210, 189, 52)


def add_edges(scene, part, color, minimum_length):
    points = vtk.vtkPoints()
    lines = vtk.vtkCellArray()
    for edge in part.Edges():
        if edge.Length() < minimum_length:
            continue
        vertices, _ = edge.sample(max(3, min(100, round(edge.Length() / 1.1))))
        lines.InsertNextCell(len(vertices))
        for point in vertices:
            lines.InsertCellPoint(points.InsertNextPoint(*point.toTuple()))
    wire = vtk.vtkPolyData()
    wire.SetPoints(points)
    wire.SetLines(lines)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(wire)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().LightingOff()
    actor.GetProperty().SetColor(*(channel / 255 for channel in color))
    actor.GetProperty().SetLineWidth(1.65)
    scene.AddActor(actor)


def render(part, eye, size, color, edge_color, minimum_edge):
    scene = vtk.vtkRenderer()
    scene.SetBackground(*(channel / 255 for channel in PAPER))
    for face in part.Faces():
        add_face(scene, face, color(face))
    add_edges(scene, part, edge_color, minimum_edge)
    eye = unit(eye)
    right = unit(np.cross([0, 0, 1], eye))
    up = np.cross(eye, right)
    vertices, _ = part.tessellate(.15, .1)
    cloud = np.array([point.toTuple() for point in vertices])
    x, y = cloud @ right, cloud @ up
    focus = (x.min() + x.max()) / 2 * right + (y.min() + y.max()) / 2 * up
    camera = scene.GetActiveCamera()
    camera.SetPosition(*(focus + 650 * eye))
    camera.SetFocalPoint(*focus)
    camera.SetViewUp(*up)
    camera.ParallelProjectionOn()
    width, height = size
    camera.SetParallelScale(.53 * max(np.ptp(y), np.ptp(x) * height / width))
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


def comparison(rendered, reference, crop):
    with urlopen(COURSE + quote(reference), timeout=20) as response:
        original = Image.open(response).convert("RGB")
    scale = original.width / 850
    image = original.crop(tuple(round(coordinate * scale) for coordinate in crop))
    width, height = rendered.size
    image.thumbnail((width, height), Image.Resampling.LANCZOS)
    page = Image.new("RGB", (width * 2 + 66, height + 98), PAPER)
    page.paste(image, (22 + (width - image.width) // 2, 52 + (height - image.height) // 2))
    page.paste(rendered, (width + 44, 52))
    pen = ImageDraw.Draw(page)
    headline = ImageFont.load_default(size=24)
    caption = ImageFont.load_default(size=17)
    pen.text((22, 16), "Course reference", font=headline, fill=INK)
    pen.text((width + 44, 16), "Reopened STEP", font=headline, fill=INK)
    pen.line((width + 33, 12, width + 33, height + 57), fill="#c5d3d2", width=1)
    pen.text((22, height + 68), "Reference: Andy Eskenazi, MIT How to CAD Almost Anything, Session 4. Independent display scales.", font=caption, fill=INK)
    return page


def render_example(folder, name, eye, size, color, edge_color, minimum_edge, reference, crop):
    target = HERE / folder
    imported = cq.importers.importStep(str(target / f"{name}.step")).val()
    result = render(imported, eye, size, color, edge_color, minimum_edge)
    result.save(target / f"{name}.png")
    comparison(result, reference, crop).save(target / f"{name}-comparison.png")


if __name__ == "__main__":
    render_example("banana", "banana", [.06, -1, .10], (730, 530), banana_color,
                   (111, 94, 34), 5, "Banana.png", (190, 82, 713, 482))
    render_example("tower", "sydney-control-tower", [.03, -1, .26], (620, 690), tower_color,
                   (57, 62, 68), 5, "Sydney Control Tower.png", (309, 86, 604, 482))
