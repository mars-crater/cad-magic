"""Constrained terrain triangulation, with closed-shell conversion for STEP."""
from collections import Counter

import cadquery as cq
import cv2
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy


def constrained_triangles(boundary, pitch):
    """Use VTK's constrained XY triangulation; reject any broken perimeter."""
    min_x, min_y = boundary.min(axis=0)
    max_x, max_y = boundary.max(axis=0)
    contour = boundary.astype(np.float32)
    grid = [(x, y) for y in np.arange(min_y + pitch / 2, max_y, pitch)
            for x in np.arange(min_x + pitch / 2, max_x, pitch)
            if cv2.pointPolygonTest(contour, (x, y), True) > 0.50]
    xy = np.vstack([boundary, grid])
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(np.pad(xy, ((0, 0), (0, 1))), deep=True))
    outline = vtk.vtkCellArray()
    outline.InsertNextCell(len(boundary))
    for index in range(len(boundary)):
        outline.InsertCellPoint(index)
    source = vtk.vtkPolyData()
    source.SetPoints(points)
    source.SetPolys(outline)
    cloud = vtk.vtkPolyData()
    cloud.SetPoints(points)
    triangulate = vtk.vtkDelaunay2D()
    triangulate.SetInputData(cloud)
    triangulate.SetSourceData(source)
    triangulate.SetTolerance(1e-8)
    triangulate.SetOffset(20)
    triangulate.Update()
    mesh = triangulate.GetOutput()
    triangles = vtk_to_numpy(mesh.GetPolys().GetConnectivityArray()).reshape(-1, 3)
    # Verify boundary recovery before converting the mesh into CAD.
    edge_counts = Counter(tuple(sorted((a, b)))
                          for i, j, k in triangles for a, b in ((i, j), (j, k), (k, i)))
    expected = {tuple(sorted((i, (i + 1) % len(boundary))))
                for i in range(len(boundary))}
    actual = {edge for edge, count in edge_counts.items() if count == 1}
    assert actual == expected and max(edge_counts.values()) == 2, (
        f'Constrained triangulation disagrees with coastline: '
        f'{len(actual - expected)} extra and {len(expected - actual)} missing edges')
    return xy, triangles


def terrain_solid(raised, boundary_count, faces, transform):
    """Turn consistent top, rim, and base faces into a sewn manifold solid."""
    vertices = [cq.Vector(*transform(x, y), z) for x, y, z in raised]
    base = [cq.Vector(vertex.x, vertex.y, 0) for vertex in vertices[:boundary_count]]

    def planar_face(points):
        return cq.Face.makeFromWires(cq.Wire.makePolygon(points, close=True))

    top = []
    for face in faces:
        a, b, c = (vertices[i] for i in face)
        points = [a, b, c] if (b - a).cross(c - a).z > 0 else [a, c, b]
        top.append(planar_face(points))
    walls = []
    for j in range(boundary_count):
        k = (j + 1) % boundary_count
        walls.append(planar_face([base[j], base[k], vertices[k], vertices[j]]))
    shell = cq.Shell.makeShell([*top, *walls, planar_face(base)])
    assert shell.Closed(), 'CAD shell leaked'
    return cq.Solid.makeSolid(shell)
