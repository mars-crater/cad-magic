"""Rebuild the unpainted anchor keychain with CadQuery, OpenCV and VTK."""
import argparse
from pathlib import Path

import cadquery as cq
import cv2
import numpy as np
import vtk
from PIL import Image

OUT = Path(__file__).resolve().parent
WIDTH = 60.0
BASE = 2.8
ANCHOR_HEIGHT = 0.85
ROPE_HEIGHT = 1.40
BORE = 6.5
ROPE = [((91, 23), (129, 38), (122, 65), (89, 78)),
        ((89, 78), (56, 91), (42, 94), (54, 106)),
        ((54, 106), (66, 118), (112, 110), (107, 130)),
        ((107, 130), (105, 142), (88, 147))]
RIM = [((80, 2), (101, 2), (115, 16), (123, 32)),
       ((123, 32), (130, 46), (126, 52), (127, 62)),
       ((127, 62), (128.7, 79), (151, 84), (151, 107)),
       ((151, 107), (151, 132), (103, 166), (80, 166)),
       ((80, 166), (57, 166), (9, 132), (9, 107)),
       ((9, 107), (9, 84), (37, 79), (37, 62)),
       ((37, 62), (37, 45), (53, 48), (56, 31)),
       ((56, 31), (59, 13), (63, 2), (80, 2))]


def xyz(point, z=0, width=WIDTH):
    return cq.Vector((point[0] - 80) * width / 142, (84 - point[1]) * width / 142, z)


def prism(edges, height):
    return cq.Solid.extrudeLinear(cq.Wire.assembleEdges(edges), [], cq.Vector(0, 0, height))


def polygon(points, z, height, width):
    wire = cq.Wire.makePolygon([xyz(p, z, width) for p in points], close=True)
    return cq.Solid.extrudeLinear(wire, [], cq.Vector(0, 0, height))


def sample_bezier(control, t):
    points = np.asarray(control, dtype=float)
    while len(points) > 1:
        points = (1 - t) * points[:-1] + t * points[1:]
    return points[0]


def stroke(segments, radius, height, width, round_caps):
    """Fit smooth offset edges to the artwork's Bézier centerlines."""
    sides = [[], []]
    for segment in segments:
        derivative = np.diff(segment, axis=0) * (len(segment) - 1)
        for t in np.linspace(0, 1, 17):
            point = sample_bezier(segment, t)
            dx, dy = sample_bezier(derivative, t)
            normal = np.array([-dy, dx]) / np.hypot(dx, dy)
            for side, sign in zip(sides, (1, -1)):
                offset = point + sign * radius * normal
                if not side or np.linalg.norm(offset - side[-1]) > 1e-6:
                    side.append(offset)
    left, right = [[xyz(p, BASE, width) for p in side] for side in sides]
    edges = [cq.Edge.makeSpline(left), cq.Edge.makeSpline(right[::-1])]
    for i, (start, end) in ((-1, (left[-1], right[-1])), (0, (right[0], left[0]))):
        if round_caps:
            segment = segments[-1] if i == -1 else segments[0]
            end_pt = np.asarray(segment[i])
            direction = end_pt - np.asarray(segment[-2 if i == -1 else 1])
            mid = end_pt + radius * direction / np.linalg.norm(direction)
            edges.append(cq.Edge.makeThreePointArc(start, xyz(mid, BASE, width), end))
        else:
            edges.append(cq.Edge.makeLine(start, end))
    return prism(edges, height)


def cylinder(point, radius_mm, z, height, width):
    return cq.Solid.makeCylinder(radius_mm, height, xyz(point, z, width))


def straight(start, end, height, width):
    return stroke([(start, end)], 5, height, width, True)


def develop(coupon, width=WIDTH, bore=BORE):
    rope = stroke(ROPE, 3, ROPE_HEIGHT, width, False)
    clearance = stroke(ROPE, 5.5, ANCHOR_HEIGHT + 0.1, width, False)
    crossbar = straight((51, 60), (109, 60), ANCHOR_HEIGHT, width)
    if coupon:
        outline = [(44, 42), (126, 42), (126, 103), (44, 103)]
        base = polygon(outline, 0, BASE, width)
        limit = polygon(outline, BASE, ROPE_HEIGHT + 0.1, width)
        stem = straight((80, 39), (80, 106), ANCHOR_HEIGHT, width)
        art = stem.fuse(crossbar).cut(clearance).intersect(limit)
        return base.fuse(art, rope.intersect(limit)).clean()

    edges = [cq.Edge.makeBezier([xyz(p, width=width) for p in segment]) for segment in RIM]
    base = prism(edges, BASE)
    eye = cylinder((80, 24), 18 * width / 142, BASE, ANCHOR_HEIGHT, width)
    stem = straight((80, 38), (80, 151), ANCHOR_HEIGHT, width)
    left = stroke([((23, 106), (34, 141), (80, 156))], 5, ANCHOR_HEIGHT, width, True)
    right = stroke([((80, 156), (126, 141), (137, 106))], 5, ANCHOR_HEIGHT, width, True)
    flukes = [polygon(points, BASE, ANCHOR_HEIGHT, width) for points in
              (((17, 118), (21, 92), (44, 109)), ((116, 109), (139, 92), (143, 118)))]
    art = eye.fuse(stem, crossbar, left, right, *flukes).cut(clearance)
    bore_tool = cylinder((80, 24), bore / 2, -0.1, BASE + ROPE_HEIGHT + 0.2, width)
    return base.fuse(art, rope).cut(bore_tool).clean()


def heightmap(shape, xmin, ymax, pixels_per_mm, resolution):
    """Rasterize upward horizontal triangles of the saved solid by elevation."""
    result = np.full(resolution, -1.0, dtype=np.float32)
    vertices, triangles = shape.tessellate(0.012, 0.10)
    vertices = np.array([v.toTuple() for v in vertices])
    planes = {}
    for indices in triangles:
        face = vertices[list(indices)]
        if np.ptp(face[:, 2]) > 1e-5:
            continue
        z = round(float(face[0, 2]), 5)
        xy = (face[:, :2] - (xmin, ymax)) * (pixels_per_mm, -pixels_per_mm)
        pixel = np.rint(16 * xy).astype(np.int32)
        planes.setdefault(z, []).append(pixel)
    for z, plane in sorted(planes.items()):
        mask = np.zeros(resolution, dtype=np.uint8)
        for triangle in plane:
            cv2.fillConvexPoly(mask, triangle, 1, shift=4)
        result[mask != 0] = z
    return result


def render_top(shape, path, coupon):
    """Orthographic render with cast shadows from the tessellated height field."""
    span = 42 if coupon else 80
    pixels = 1100
    ppm = pixels / span
    center = shape.BoundingBox().center
    depth = heightmap(shape, center.x - span / 2, center.y + span / 2, ppm, (pixels, pixels))
    ys, xs = np.indices(depth.shape, dtype=np.float32)
    shadow = np.zeros_like(depth, dtype=bool)
    # Cast a low-angle key light from upper left; flat faces retain one material.
    for step in range(2, int(ppm * 9), 2):
        upstream = cv2.remap(depth, xs - step, ys - 0.62 * step, cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=-1)
        shadow |= upstream > depth + 0.045 + 0.48 * step / ppm
    softness = cv2.GaussianBlur(shadow.astype(np.float32), (0, 0), 1.4)
    up_left = cv2.remap(depth, xs - 3, ys - 2, cv2.INTER_NEAREST,
                       borderMode=cv2.BORDER_CONSTANT, borderValue=-1)
    rim_light = cv2.GaussianBlur((depth > up_left + 0.2).astype(np.float32), (0, 0), 0.9)
    luminance = 0.82 - 0.28 * softness + 0.14 * rim_light
    material = luminance[:, :, None] * np.array([221, 222, 215])
    rgb = np.where((depth >= 0)[:, :, None], material, [43, 48, 53])
    img = Image.fromarray(rgb.astype(np.uint8))
    if coupon:
        # A physical-size orthographic print at 300 DPI, if printed at 100%.
        image_pixels = round(span / 25.4 * 300)
        img.resize((image_pixels, image_pixels), Image.Resampling.LANCZOS).save(
            OUT / "coupon-1to1.png", dpi=(300, 300))
    img.save(path)


def render(shape, path, oblique=False, coupon=False):
    if not oblique:
        render_top(shape, path, coupon)
        return
    vertices, triangles = shape.tessellate(0.035, 0.12)
    vpoints = vtk.vtkPoints()
    for v in vertices:
        vpoints.InsertNextPoint(*v.toTuple())
    cells = vtk.vtkCellArray()
    for tri in triangles:
        cells.InsertNextCell(3, tri)
    data = vtk.vtkPolyData()
    data.SetPoints(vpoints)
    data.SetPolys(cells)
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(data)
    normals.ComputePointNormalsOn()
    normals.ConsistencyOn()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.78, 0.78, 0.76)
    actor.GetProperty().SetAmbient(0.30)
    actor.GetProperty().SetDiffuse(0.72)
    actor.GetProperty().SetSpecular(0.12)
    actor.GetProperty().SetSpecularPower(24)
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.17, 0.19, 0.21)
    renderer.AddActor(actor)
    renderer.UseSSAOOn()
    renderer.SetSSAORadius(2.6)
    renderer.SetSSAOBias(0.045)
    renderer.SetSSAOKernelSize(64)
    renderer.SSAOBlurOn()
    renderer.AutomaticLightCreationOff()
    box = shape.BoundingBox()
    focus = tuple(box.center.toTuple())
    for position, intensity in [((-65, 50, 35), 0.95), ((35, -28, 50), 0.32)]:
        light = vtk.vtkLight()
        light.SetLightTypeToSceneLight()
        light.SetPosition(*position)
        light.SetFocalPoint(*focus)
        light.SetIntensity(intensity)
        renderer.AddLight(light)
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(*focus)
    camera.SetPosition(*np.add(focus, (55, -76, 110) if oblique else (0, 0, 120)))
    camera.SetViewUp(0, 1, 0)
    camera.ParallelProjectionOn()
    camera.SetParallelScale(22 if coupon else 41)
    renderer.ResetCameraClippingRange()
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(1000, 1000)
    window.SetMultiSamples(8)
    window.AddRenderer(renderer)
    window.Render()
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(path))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()
    window.Finalize()


def export_reopen(shape, stem):
    filename = OUT / f"{stem}.step"
    cq.exporters.export(shape, str(filename))
    reopened = cq.importers.importStep(str(filename)).val()
    for item in (shape, reopened):
        assert len(item.Solids()) == 1 and item.isValid()
        assert abs(item.Volume() - shape.Volume()) < 0.005
    return reopened


if __name__ == "__main__":
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("stage", choices=("coupon", "final"))
    args = argp.parse_args()
    coupon = args.stage == "coupon"
    model = export_reopen(develop(coupon), args.stage)
    print(args.stage, model.Volume(), model.BoundingBox().xlen, model.BoundingBox().zlen)
    if coupon:
        render(model, OUT / "coupon-oblique.png", oblique=True, coupon=True)
        render(model, OUT / "coupon-top.png", coupon=True)
    else:
        render(model, OUT / "top.png")
        render(model, OUT / "oblique.png", oblique=True)
