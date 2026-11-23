"""Build and verify the anchor keychain. Run with ../.venv/bin/python build.py."""
from dataclasses import dataclass, replace
from io import BytesIO
from pathlib import Path

import cairosvg
import cadquery as cq
import cv2
import numpy as np
from PIL import Image
import vtk

HERE = Path(__file__).resolve().parent
SVG = HERE.parent / "reference.svg"
PIXELS_PER_UNIT = 5


@dataclass(frozen=True)
class Design:
    width: float = 60.0
    height: float = 66.0
    corner_radius: float = 10.0
    rim_radius: float = 0.45
    base: float = 3.2
    anchor: float = 0.9
    rope: float = 0.52
    svg_scale: float = 0.38
    bore: float = 5.5
    trace_error: float = 0.065

    def xy(self, svg_x, svg_y):
        return ((svg_x - 80) * self.svg_scale, (89 - svg_y) * self.svg_scale)


def source_masks():
    png = cairosvg.svg2png(
        url=str(SVG), output_width=160 * PIXELS_PER_UNIT,
        output_height=180 * PIXELS_PER_UNIT,
    )
    pixels = np.array(Image.open(BytesIO(png)).convert("RGB")).astype(np.int16)
    palette = np.array([[255, 255, 255], [39, 57, 71], [152, 100, 56]])
    nearest = np.argmin(np.sum((pixels[:, :, None] - palette) ** 2, axis=-1), axis=-1)
    return nearest == 1, nearest == 2


def trace(mask, d, height):
    contours, tree = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    parents = tree[0, :, 3]
    wires = {}
    for i, contour in enumerate(contours):
        if cv2.contourArea(contour) < 8:
            continue
        polygon = cv2.approxPolyDP(contour, d.trace_error * PIXELS_PER_UNIT / d.svg_scale, True)
        points = [cq.Vector(*d.xy((x + 0.5) / PIXELS_PER_UNIT,
                                  (y + 0.5) / PIXELS_PER_UNIT), d.base)
                  for x, y in polygon[:, 0]]
        if len(points) >= 3:
            wires[i] = cq.Wire.makePolygon(points, close=True)
    return [cq.Solid.extrudeLinear(wire, [wires[j] for j in wires if parents[j] == i],
                                   (0, 0, height))
            for i, wire in wires.items() if parents[i] == -1]


def build(d, masks):
    slab = (cq.Workplane("XY").rect(d.width, d.height).extrude(d.base)
            .edges("|Z").fillet(d.corner_radius)
            .edges("not |Z").fillet(d.rim_radius).val())
    feature_solids = trace(masks[0], d, d.anchor) + trace(masks[1], d, d.rope)
    bore = cq.Solid.makeCylinder(d.bore / 2, d.base + d.anchor + 2,
                                 cq.Vector(*d.xy(80, 24), -1))
    return slab.fuse(*feature_solids).cut(bore).clean()


def section_mask(shape, d, z, mask_shape):
    section = cq.Workplane("XY").newObject([shape]).section(z)
    result = np.zeros(mask_shape, dtype=np.uint8)
    for face in section.val().Faces():
        positions, triangles = face.tessellate(0.012)
        pixels = np.array([((p.x / d.svg_scale + 80) * PIXELS_PER_UNIT - 0.5,
                            (89 - p.y / d.svg_scale) * PIXELS_PER_UNIT - 0.5)
                           for p in positions])
        pixels = np.rint(pixels * 256).astype(np.int32)
        for tri in triangles:
            cv2.fillConvexPoly(result, pixels[list(tri)], 1, shift=8)
    return result.astype(bool)


def verify(shape, d, masks):
    assert shape.isValid() and len(shape.Solids()) == 1
    bounds = shape.BoundingBox()
    actual = (bounds.xlen, bounds.ylen, bounds.zlen)
    assert np.allclose(actual, (d.width, d.height, d.base + d.anchor), atol=1e-6)
    x, y = d.xy(80, 24)
    bore_faces = []
    for face in shape.Faces():
        if face.geomType() == "CYLINDER":
            cylinder = face._geomAdaptor().Cylinder()
            axis = cylinder.Axis().Location()
            if abs(axis.X() - x) < 1e-6 and abs(axis.Y() - y) < 1e-6:
                bore_faces.append((cylinder.Radius(), face.BoundingBox()))
    assert len(bore_faces) == 1
    radius, bore_span = bore_faces[0]
    assert abs(radius * 2 - d.bore) < 1e-6
    assert abs(bore_span.zmin) < 1e-6 and abs(bore_span.zmax - d.base) < 1e-6
    for z in (0.08, d.base / 2, d.base - 0.08):
        assert not shape.isInside((x, y, z))
        assert not shape.isInside((x + radius - 0.08, y, z))
        assert shape.isInside((x + radius + 0.08, y, z))

    anchor_slice = section_mask(shape, d, d.base + (d.rope + d.anchor) / 2, masks[0].shape)
    all_slice = section_mask(shape, d, d.base + d.rope / 2, masks[0].shape)
    rope_slice = all_slice & ~anchor_slice
    scores = []
    for expected, observed in zip((*masks, masks[0] | masks[1]), (anchor_slice, rope_slice, all_slice)):
        scores.append(np.count_nonzero(expected & observed) / np.count_nonzero(expected | observed))
    assert min(scores) > 0.87, scores
    return actual, 2 * radius, scores, (anchor_slice, rope_slice)


def render(shape, name, camera_position):
    points, triangles = shape.tessellate(0.025, 0.12)
    vertices = vtk.vtkPoints()
    for point in points:
        vertices.InsertNextPoint(*point.toTuple())
    cells = vtk.vtkCellArray()
    for triangle in triangles:
        cells.InsertNextCell(3, triangle)
    mesh = vtk.vtkPolyData()
    mesh.SetPoints(vertices)
    mesh.SetPolys(cells)
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(mesh)
    normals.SplittingOff()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.79, 0.71, 0.59)
    actor.GetProperty().SetAmbient(0.38)
    actor.GetProperty().SetDiffuse(0.75)
    actor.GetProperty().SetSpecular(0.13)
    actor.GetProperty().SetSpecularPower(30)

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.07, 0.10, 0.13)
    renderer.SetBackground2(0.14, 0.20, 0.24)
    renderer.GradientBackgroundOn()
    renderer.AddActor(actor)
    renderer.UseSSAOOn()
    renderer.SetSSAORadius(2.6)
    renderer.SetSSAOBias(0.035)
    renderer.SetSSAOKernelSize(96)
    renderer.SSAOBlurOn()
    for position, intensity in [((-45, 35, 65), 0.84), ((50, -25, 42), 0.28)]:
        light = vtk.vtkLight()
        light.SetLightTypeToSceneLight()
        light.SetPosition(*position)
        light.SetFocalPoint(0, 0, 0)
        light.SetIntensity(intensity)
        renderer.AddLight(light)
    camera = renderer.GetActiveCamera()
    camera.ParallelProjectionOn()
    camera.SetParallelScale(41)
    camera.SetPosition(*camera_position)
    camera.SetFocalPoint(0, 0, 1.6)
    camera.SetViewUp(0, 1, 0)
    renderer.ResetCameraClippingRange()
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetMultiSamples(0)
    window.SetSize(1200, 1200)
    window.AddRenderer(renderer)
    window.Render()
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(HERE / name))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()
    window.Finalize()


def main():
    d = Design()
    masks = source_masks()
    step = HERE / "final.step"
    model = build(d, masks)
    verify(model, d, masks)
    cq.exporters.export(model, str(step))
    restored = cq.importers.importStep(str(step)).val()
    dimensions, bore, scores, restored_masks = verify(restored, d, masks)
    variant = replace(d, bore=5.0)
    variant_size, variant_bore, _, variant_masks = verify(build(variant, masks), variant, masks)
    assert all(np.array_equal(a, b) for a, b in zip(restored_masks, variant_masks))
    render(restored, "top.png", (0, 0, 100))
    render(restored, "oblique.png", (62, -78, 105))
    print(f"STEP: one valid solid; XYZ mm {dimensions}; axial through-bore Ø{bore:.3f} mm")
    print("Source/STEP section mask IoU (anchor, rope, union): "
          + ", ".join(f"{value:.2%}" for value in scores))
    print(f"Variant Ø{variant_bore:.3f} mm: XYZ {variant_size}; relief masks unchanged")


if __name__ == "__main__":
    main()
