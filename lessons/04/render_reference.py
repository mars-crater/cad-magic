"""Render a reopened STEP and optionally compare with an instructor screenshot."""
import argparse
from pathlib import Path

import cadquery as cq
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy

from hull.render import unit, PAPER, INK

HERE = Path(__file__).resolve().parent
VIEWS = {
    "crane": ("crane", (.46, -.84, .30), 0, (720, 830), (1060, 331, 2300, 1660)),
    "racquet": ("squash-racquet", (.45, .13, .89), 65, (960, 600), (525, 370, 2745, 1605)),
}


def render(part, name, facing, roll, size):
    scene = vtk.vtkRenderer()
    scene.SetBackground(*(v / 255 for v in PAPER))
    points, triangles = part.tessellate(.14, .27)
    vertices = np.array([point.toTuple() for point in points])
    triangles = np.asarray(triangles, dtype=np.int64)
    x, _, z = vertices[triangles].mean(axis=1).T
    if name == "crane":
        dark = ((z < 3) & (abs(x) < 14)) | (
            (z > 287) & (z < 305) & (abs(x) < 11)
        ) | ((x < -35) & (z < 308))
        colors = np.where(dark[:, None], (85, 102, 116), (198, 164, 45))
    else:
        y = vertices[triangles, 1].mean(axis=1)
        colors = np.where((y < 158)[:, None], (96, 111, 125), (43, 76, 142))
    mesh = vtk.vtkPolyData()
    vtk_points = vtk.vtkPoints()
    vtk_points.SetData(numpy_to_vtk(vertices, deep=True))
    mesh.SetPoints(vtk_points)
    cells = vtk.vtkCellArray()
    offsets = np.arange(0, 3 * len(triangles) + 1, 3, dtype=np.int64)
    cells.SetData(numpy_to_vtkIdTypeArray(offsets, deep=True),
                  numpy_to_vtkIdTypeArray(triangles.ravel(), deep=True))
    mesh.SetPolys(cells)
    mesh.GetCellData().SetScalars(numpy_to_vtk(colors.astype(np.uint8), deep=True))
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(mesh)
    normals.SplittingOff()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    mapper.SetScalarModeToUseCellData()
    mapper.SetColorModeToDirectScalars()
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetAmbient(.35)
    actor.GetProperty().SetDiffuse(.7)
    scene.AddActor(actor)

    eye = unit(facing)
    right = unit(np.cross([0, 0, 1] if name == "crane" else [0, 1, 0], eye))
    up = np.cross(eye, right)
    angle = np.deg2rad(roll)
    right, up = right * np.cos(angle) - up * np.sin(angle), up * np.cos(angle) + right * np.sin(angle)
    span_x, span_y = vertices @ right, vertices @ up
    focus = (span_x.min() + span_x.max()) / 2 * right + (span_y.min() + span_y.max()) / 2 * up
    camera = scene.GetActiveCamera()
    camera.SetPosition(*(focus + 1000 * eye))
    camera.SetFocalPoint(*focus)
    camera.SetViewUp(*up)
    camera.ParallelProjectionOn()
    width, height = size
    camera.SetParallelScale(.54 * max(np.ptp(span_y), np.ptp(span_x) * height / width))
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
    result = Image.fromarray(pixels.reshape(2 * height, 2 * width, 3)[::-1])
    window.Finalize()
    return result.resize(size, Image.Resampling.LANCZOS)


def comparison(reference, model, crop):
    width, height = model.size
    page = Image.new("RGB", (2 * width + 54, height + 100), PAPER)
    source = Image.open(reference).convert("RGB").crop(crop)
    source.thumbnail((width, height), Image.Resampling.LANCZOS)
    page.paste(source, (18 + (width - source.width) // 2, 54 + (height - source.height) // 2))
    page.paste(model, (36 + width, 54))
    pen = ImageDraw.Draw(page)
    label = ImageFont.load_default(size=23)
    pen.text((18, 18), "COURSE CAD · ANDY ESKENAZI", font=label, fill=INK)
    pen.text((36 + width, 18), "REOPENED STEP · CADQUERY", font=label, fill=INK)
    pen.text((18, height + 65), "Independent display scales; approximate matched orientation.",
             font=label, fill=INK)
    return page


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exercise", choices=VIEWS)
    parser.add_argument("--reference", type=Path, help="Original course CAD screenshot, downloaded separately")
    args = parser.parse_args()
    filename, facing, roll, size, crop = VIEWS[args.exercise]
    output = HERE / args.exercise
    part = cq.importers.importStep(str(output / f"{filename}.step")).val()
    result = render(part, args.exercise, facing, roll, size)
    result.save(output / f"{filename}.png")
    if args.exercise == "racquet":
        clip = cq.Solid.makeBox(30, 105, 30, cq.Vector(80, 480, -15))
        detail = part.intersect(clip)
        render(detail, "racquet", (.96, .03, .27), 90, (820, 240)).save(
            output / f"{filename}-grommets.png")
    if args.reference:
        comparison(args.reference, result, crop).save(output / f"{filename}-comparison.png")
