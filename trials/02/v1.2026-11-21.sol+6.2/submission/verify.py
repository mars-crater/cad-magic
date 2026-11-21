"""Reopen the STEP solids, compare mesh sections with source masks, and render."""
import argparse
import json

import cadquery as cq
import cv2
import numpy as np
from PIL import Image, ImageDraw
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy

from build import (BORE, CREST_BASE, FIELD_HEIGHT, GOLD_HEIGHT, ROOT, OUT,
                   CREST_WIDTH, MADEIRA_WIDTH, crest, crest_source, madeira,
                   madeira_source)

PANEL = (760, 540)
STYLE = {
    'madeira': {'center': (0, 0, 0), 'scale': 67, 'oblique': (38, -125, 110)},
    'crest': {'center': (0, 6, 0), 'scale': 46, 'oblique': (39, -53, 105)},
}


def to_mesh(shape, tolerance):
    vertices, triangles = shape.tessellate(tolerance, 0.12)
    points = np.array([p.toTuple() for p in vertices])
    faces = np.array(triangles, dtype=np.int64)
    geometry = vtk.vtkPolyData()
    vtk_points = vtk.vtkPoints()
    vtk_points.SetData(numpy_to_vtk(points, deep=True))
    geometry.SetPoints(vtk_points)
    vtk_cells = vtk.vtkCellArray()
    offsets = np.arange(0, 3 * (len(faces) + 1), 3, dtype=np.int64)
    vtk_cells.SetData(numpy_to_vtkIdTypeArray(offsets, deep=True),
                      numpy_to_vtkIdTypeArray(faces.ravel(), deep=True))
    geometry.SetPolys(vtk_cells)
    return geometry, points, faces


def render(mesh, part, view):
    mapper = vtk.vtkPolyDataMapper()
    # CAD faces share geometric locations but have separate tessellation indices.
    # Preserve their exact normals at sharp breaks rather than smooth those edges.
    mapper.SetInputData(mesh)
    if part == 'crest' and view == 'top':
        # Depth tones make parallel planes separately visible in a normal view.
        display_mesh = vtk.vtkPolyData()
        display_mesh.ShallowCopy(mesh)
        z = vtk_to_numpy(mesh.GetPoints().GetData())[:, 2]
        gray = np.interp(z, [0, CREST_BASE, CREST_BASE + FIELD_HEIGHT,
                            CREST_BASE + GOLD_HEIGHT], [103, 103, 153, 237])
        tones = numpy_to_vtk(np.repeat(gray.astype(np.uint8)[:, None], 3, axis=1),
                             deep=True)
        display_mesh.GetPointData().SetScalars(tones)
        mapper.SetInputData(display_mesh)
        mapper.SetColorModeToDirectScalars()
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.80, 0.80, 0.80)
    actor.GetProperty().SetAmbient(0.26)
    actor.GetProperty().SetDiffuse(0.74)
    actor.GetProperty().SetSpecular(0.06)
    actor.GetProperty().SetInterpolationToPhong()
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.10, 0.10, 0.10)
    renderer.AddActor(actor)
    if part == 'crest' and view == 'oblique':
        renderer.UseSSAOOn()
        renderer.SetSSAORadius(2.0)
        renderer.SetSSAOBias(0.04)
        renderer.SetSSAOKernelSize(64)
    spec = STYLE[part]
    camera = renderer.GetActiveCamera()
    camera.ParallelProjectionOn()
    camera.SetParallelScale(spec['scale'])
    center = np.array(spec['center'])
    direction = (0, 0, 170) if view == 'top' else spec['oblique']
    camera.SetFocalPoint(*center)
    camera.SetPosition(*(center + direction))
    camera.SetViewUp(0, 1, 0)
    renderer.ResetCameraClippingRange()
    for position, intensity in [((-70, 85, 100), 0.93), ((40, -45, 80), 0.26)]:
        light = vtk.vtkLight()
        light.SetLightTypeToSceneLight()
        light.SetPosition(*position)
        light.SetFocalPoint(*center)
        light.SetIntensity(intensity)
        renderer.AddLight(light)
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(*(2 * px for px in PANEL))
    window.AddRenderer(renderer)
    window.Render()
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.Update()
    output = capture.GetOutput()
    w, h, _ = output.GetDimensions()
    pixels = vtk_to_numpy(output.GetPointData().GetScalars())
    image = Image.fromarray(pixels.reshape(h, w, 3)[::-1]).resize(
        PANEL, Image.Resampling.LANCZOS)
    window.Finalize()
    return image


def reference_panel(part, transform):
    if part == 'madeira':
        reference = Image.open(ROOT / 'inputs/madeira.png').convert('RGBA')
        # Sea is black in the supplied height map; leave that intact.
    else:
        original = Image.open(ROOT / 'crest.png').convert('RGBA')
        reference = Image.new('RGBA', (original.width + 16, original.height + 16))
        reference.paste(original, (8, 8))
    cx, cy, _ = STYLE[part]['center']
    px_per_mm = PANEL[1] / (2 * STYLE[part]['scale'])
    x0, y0 = transform(0, 0)
    x1, y1 = transform(reference.width - 1, reference.height - 1)
    panel = Image.new('RGBA', PANEL, (26, 26, 26, 255))
    panel.alpha_composite(reference.resize((round((x1 - x0) * px_per_mm),
                                            round((y0 - y1) * px_per_mm)),
                                           Image.Resampling.LANCZOS),
                          (round(PANEL[0] / 2 + (x0 - cx) * px_per_mm),
                           round(PANEL[1] / 2 - (y0 - cy) * px_per_mm)))
    return panel.convert('RGB')


def make_renders(part, mesh, transform):
    orthographic = render(mesh, part, 'top')
    orthographic.save(OUT / f'{part}-top.png')
    render(mesh, part, 'oblique').save(OUT / f'{part}-oblique.png')
    comparison = Image.new('RGB', (2 * PANEL[0], PANEL[1] + 38), '#1d1d1d')
    comparison.paste(reference_panel(part, transform), (0, 38))
    comparison.paste(orthographic, (PANEL[0], 38))
    labels = ImageDraw.Draw(comparison)
    labels.text((12, 11), 'Supplied reference', fill='white', font_size=15)
    title = 'Reopened STEP · same orientation and scale'
    if part == 'crest':
        title += ' · geometry heights shown in grayscale'
    labels.text((PANEL[0] + 12, 11), title, fill='white', font_size=15)
    comparison.save(OUT / f'{part}-comparison.png')


def projection(points, faces, transform, size, level=None):
    x, y = transform(0, 0)
    scale = transform(1, 0)[0] - x
    projected = (points[:, :2] - (x, y)) / (scale, -scale)
    supersample = 4
    layer = np.zeros(tuple(n * supersample for n in size), dtype=np.uint8)
    if level is not None:
        faces = faces[np.all(np.isclose(points[faces, 2], level, atol=0.00001), axis=1)]
    for triangle in faces:
        pixels = np.rint(projected[triangle] * (256 * supersample)).astype(np.int32)
        cv2.fillConvexPoly(layer, pixels, 1, shift=8)
    return layer[::supersample, ::supersample].astype(bool)


def overlap(a, b):
    return round(float((a & b).sum() / (a | b).sum()), 4)


def locator(mesh):
    tree = vtk.vtkStaticCellLocator()
    tree.SetDataSet(mesh)
    tree.BuildLocator()
    return tree


def height(tree, x, y):
    t = vtk.mutable(0.0)
    pos, coord = [0.0] * 3, [0.0] * 3
    sub_id, cell = vtk.mutable(0), vtk.mutable(0)
    found = tree.IntersectWithLine((x, y, 60), (x, y, -1), 1e-7, t, pos,
                                   coord, sub_id, cell)
    return pos[2] if found else None


def check_madeira(mesh, points, faces):
    gray, _, transform = madeira_source(MADEIRA_WIDTH)
    footprint = projection(points, faces, transform, gray.shape)
    # Compare coastline to original threshold pixels, not the simplified build outline.
    _, labels, stats, _ = cv2.connectedComponentsWithStats(np.uint8(gray > 2))
    source = labels == (1 + stats[1:, 4].argmax())
    boxes = {'eastern peninsula': (179, 56, 239, 83)}
    result = {'main-island coastline IoU': overlap(footprint, source)}
    for name, (x0, y0, x1, y1) in boxes.items():
        result[f'{name} IoU'] = overlap(footprint[y0:y1, x0:x1], source[y0:y1, x0:x1])
    tree = locator(mesh)
    paired = [(int(gray[y, x]), height(tree, *transform(x, y)))
              for y, x in np.argwhere(source)[::5]]
    paired = [(pixel, z) for pixel, z in paired if z is not None]
    result['sampled source elevation vs STEP height Pearson r'] = round(
        float(np.corrcoef(np.asarray(paired).T)[0, 1]), 4)
    result['sample count'] = len(paired)
    samples = {'central crest': (130, 60), 'south slope': (130, 90),
               'south descent': (130, 100), 'south valley': (120, 80),
               'south valley west bank': (110, 80), 'south valley east bank': (130, 80),
               'north valley': (100, 50), 'north valley west bank': (90, 50),
               'north valley east bank': (110, 50), 'east headland': (220, 70)}
    result['landmarks (pixel x,y; shade; STEP height)'] = {}
    for name, (x, y) in samples.items():
        z = height(tree, *transform(x, y))
        result['landmarks (pixel x,y; shade; STEP height)'][name] = [
            x, y, int(gray[y, x]), None if z is None else round(z, 3)]
    return result, transform


def check_crest(shape, mesh, points, faces):
    opaque, gold, transform = crest_source(CREST_WIDTH)
    raised = projection(points, faces, transform, gold.shape, CREST_BASE + GOLD_HEIGHT)
    field = projection(points, faces, transform, gold.shape, CREST_BASE + FIELD_HEIGHT)
    result = {'crest field + raised IoU': overlap(field | raised, opaque),
              'raised gold IoU': overlap(raised, gold)}
    regions = {'ship': (103, 94, 194, 128), 'devil': (110, 130, 187, 244),
               'left football': (8, 145, 62, 195), 'right football': (248, 145, 300, 195),
               'upper banner': (24, 25, 288, 140), 'lower banner': (36, 222, 277, 296),
               'MANCHESTER': (35, 33, 277, 120), 'UNITED': (76, 236, 239, 281)}
    result['region gold IoUs (approximate bounding windows)'] = {}
    for name, (x0, y0, x1, y1) in regions.items():
        sl = np.s_[y0:y1, x0:x1]
        result['region gold IoUs (approximate bounding windows)'][name] = overlap(
            raised[sl], gold[sl])
    circles = [edge for edge in shape.Edges() if edge.geomType() == 'CIRCLE'
               and abs(edge.radius() - BORE / 2) < 1e-6]
    assert len(circles) == 2, 'Bore does not have two complete circular boundaries'
    bore_ends = sorted([edge.Center().toTuple() for edge in circles], key=lambda p: p[2])
    center = bore_ends[0][:2]
    alpha_top = transform(0, np.where(opaque)[0].min())[1]
    tree = locator(mesh)
    assert height(tree, *center) is None
    assert height(tree, center[0] + BORE / 2 + 0.5, center[1]) is not None
    result.update({'bore diameter mm': round(circles[0].radius() * 2, 6),
                   'bore rim z levels mm': [round(c[2], 5) for c in bore_ends],
                   'bore center XY mm': [round(v, 5) for v in center],
                   'through ray clear': True,
                   'bore lower edge above reference artwork mm': round(
                       center[1] - BORE / 2 - alpha_top, 4)})
    return result, transform


def run(part):
    reopened = cq.importers.importStep(str(OUT / f'{part}.step'))
    solids = reopened.solids().vals()
    assert len(solids) == 1
    shape = solids[0]
    assert shape.isValid()
    # Measure analytic extrema before triangulation adds tessellation deflection.
    box = shape.BoundingBox()
    dimensions = [round(d, 5) for d in (box.xlen, box.ylen, box.zlen)]
    mesh, points, faces = to_mesh(shape, 0.05 if part == 'madeira' else 0.025)
    if part == 'madeira':
        result, transform = check_madeira(mesh, points, faces)
    else:
        result, transform = check_crest(shape, mesh, points, faces)
    make_renders(part, mesh, transform)
    result.update({'solid count': len(solids), 'is valid': True,
                   'dimensions XYZ mm': dimensions, 'volume mm3': round(shape.Volume(), 3),
                   'mesh triangles': len(faces)})
    record = json.dumps(result, indent=2) + '\n'
    (OUT / f'{part}-checks.json').write_text(record)
    print(record, flush=True)


def variants():
    part = madeira(width=160)
    assert part.isValid() and len(part.Solids()) == 1
    box = part.BoundingBox()
    assert abs(box.xlen - 160) < 1e-6 and abs(box.zlen - 28) < 1e-6
    keychain, expected_center = crest(bore=6.0)
    circles = [edge for edge in keychain.Edges() if edge.geomType() == 'CIRCLE'
               and abs(edge.radius() - 3.0) < 1e-6]
    outer = [edge for edge in keychain.Edges() if edge.geomType() == 'CIRCLE'
             and abs(edge.radius() - 5.5) < 1e-6]
    assert keychain.isValid() and len(keychain.Solids()) == 1
    assert len(circles) == len(outer) == 2
    for edge in circles + outer:
        # Positions at half parameter are not centers on the partial outer rim.
        center = edge._geomAdaptor().Circle().Location()
        assert np.allclose([center.X(), center.Y()], expected_center, atol=1e-6)
    result = {'Madeira width 145 -> 160 mm': {'dimensions XYZ mm':
                                              [box.xlen, box.ylen, box.zlen]},
              'crest bore 5 -> 6 mm': {'bore diameter mm': 6.0,
                                      'loop outer diameter mm': 11.0,
                                      'unchanged concentric center XY mm': expected_center}}
    (OUT / 'variant-checks.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('part', choices=('madeira', 'crest', 'both'), default='both', nargs='?')
    parser.add_argument('--variants', action='store_true',
                        help='also rebuild dimensional edits in memory')
    args = parser.parse_args()
    for name in ('madeira', 'crest'):
        if args.part in (name, 'both'):
            run(name)
    if args.variants:
        variants()
