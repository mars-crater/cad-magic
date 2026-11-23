"""Render two orthographic cameras from the imported colored STEP, not source."""
from argparse import ArgumentParser
from pathlib import Path

import cadquery as cq
import vtk


def mesh_actor(shape, color):
    points = vtk.vtkPoints()
    cells = vtk.vtkCellArray()
    vertices, triangles = shape.tessellate(0.07, 0.13)
    for vertex in vertices:
        points.InsertNextPoint(*vertex.toTuple())
    for triangle in triangles:
        cells.InsertNextCell(3, triangle)
    poly = vtk.vtkPolyData()
    poly.SetPoints(points)
    poly.SetPolys(cells)
    clean = vtk.vtkCleanPolyData()
    clean.SetInputData(poly)
    clean.SetTolerance(1.0e-7)
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(clean.GetOutputPort())
    normals.SetFeatureAngle(33)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    finish = actor.GetProperty()
    finish.SetColor(*color[:3])
    finish.SetAmbient(0.35)
    finish.SetDiffuse(0.69)
    finish.SetSpecular(0.48)
    finish.SetSpecularPower(36)
    return actor


def render(step, output):
    assembly = cq.Assembly.importStep(str(step))
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.94, 0.96, 0.98)
    renderer.SetBackground2(0.81, 0.85, 0.90)
    renderer.GradientBackgroundOn()
    for shape, name, location, color in assembly:
        if color is None:
            raise ValueError(f"STEP node {name} lacks color")
        renderer.AddActor(mesh_actor(shape.moved(location), color.toTuple()))
    for position, intensity in (((-45, -20, 95), 0.9), ((60, 40, 45), 0.46),
                                ((0, -35, -75), 0.25)):
        light = vtk.vtkLight()
        light.SetPosition(*position)
        light.SetFocalPoint(0, 0, 0)
        light.SetIntensity(intensity)
        renderer.AddLight(light)
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(1600, 1200)
    window.SetMultiSamples(8)
    window.AddRenderer(renderer)
    for label, position, up in (
        ("top", (0, 0, 150), (0, 1, 0)),
        ("oblique", (-45, -109, 88), (0, 0, 1)),
    ):
        camera = renderer.GetActiveCamera()
        camera.SetPosition(*position)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(*up)
        camera.ParallelProjectionOn()
        camera.SetParallelScale(66)
        renderer.ResetCameraClippingRange()
        window.Render()
        capture = vtk.vtkWindowToImageFilter()
        capture.SetInput(window)
        capture.ReadFrontBufferOff()
        writer = vtk.vtkPNGWriter()
        writer.SetInputConnection(capture.GetOutputPort())
        writer.SetFileName(str(output / f"{label}.png"))
        writer.Write()


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("step", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    render(args.step, args.output)
