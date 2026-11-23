"""Roll staggered rows of hexagons into an open ball-and-stick assembly (mm)."""
import math
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

import cadquery as cq
import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
PITCH = 3.0  # Nominal bond length measured on the unrolled sheet
NODE_RADIUS = 0.52
BOND_RADIUS = 0.25
HEXAGON = ((0, 2), (1, 1), (1, -1), (0, -2), (-1, -1), (-1, 1))


def lattice(sectors, rows):
    # Integer coordinates are half-pitches. Wrap *before* deduplicating:
    # a corner at the far edge and its image at the origin are one joint.
    edges = set()
    for row in range(rows):
        for sector in range(sectors):
            corners = [((2 * sector + row % 2 + dx) % (2 * sectors), 3 * row + dz)
                       for dx, dz in HEXAGON]
            for start, end in zip(corners, corners[1:] + corners[:1]):
                edges.add(tuple(sorted((start, end))))
    radius = sectors * math.sqrt(3) * PITCH / (2 * math.pi)
    nodes = {}
    for index in sorted({node for edge in edges for node in edge}):
        angle = math.pi * index[0] / sectors
        nodes[index] = cq.Vector(radius * math.cos(angle), radius * math.sin(angle),
                                 PITCH * index[1] / 2)
    parts = [cq.Solid.makeSphere(NODE_RADIUS, point, angleDegrees1=-90)
             for point in nodes.values()]
    for start, end in sorted(edges):
        delta = nodes[end] - nodes[start]
        parts.append(cq.Solid.makeCylinder(BOND_RADIUS, delta.Length, nodes[start], delta))
    return cq.Compound.makeCompound(parts)


def check(path, sectors, rows):
    """Recover the network from translated STEP surface geometry, not sketch indices."""
    part = cq.importers.importStep(str(path)).val()
    spheres, endpoints = [], []
    for body in part.Solids():
        assert body.isValid()
        faces = body.Faces()
        if len(faces) == 1:
            assert faces[0].geomType() == "SPHERE"
            spheres.append(body.Center().toTuple())
        else:
            caps = [f.Center().toTuple() for f in faces if f.geomType() == "PLANE"]
            assert len(caps) == 2 and len(faces) == 3
            endpoints.append(caps)
    distances, indices = cKDTree(spheres).query(endpoints)
    assert distances.max() < 1e-6
    edges = {tuple(sorted(edge)) for edge in indices}
    assert len(edges) == len(endpoints) == sectors * (3 * rows + 2)
    assert len(spheres) == 2 * sectors * (rows + 1)
    graph = [set() for _ in spheres]
    for a, b in edges:
        graph[a].add(b)
        graph[b].add(a)
    seen, pending = set(), [0]
    while pending:
        vertex = pending.pop()
        if vertex not in seen:
            seen.add(vertex)
            pending.extend(graph[vertex] - seen)
    assert len(seen) == len(spheres)
    assert Counter(map(len, graph)) == {2: 2 * sectors, 3: len(spheres) - 2 * sectors}

    # Every hexagon, including those across angle zero, is a simple six-edge
    # cycle. For these circumference counts no cycle of six encircles the tube.
    def cycles(node, path):
        if len(path) == 6:
            return int(path[0] in graph[node])
        return sum(cycles(n, path + [n]) for n in graph[node] if n not in path)
    hexagons = sum(cycles(i, [i]) for i in range(len(graph))) // 12
    assert hexagons == sectors * rows
    xyz = np.array(spheres)
    radii = np.linalg.norm(xyz[:, :2], axis=1)
    assert np.ptp(radii) < 1e-6
    lengths = np.linalg.norm(np.diff(endpoints, axis=1)[:, 0], axis=1)
    # Inner ends of chords bound the clear axial passage: no disk, no plug.
    midpoints = np.mean(endpoints, axis=1)
    clearance = min(radii.min() - NODE_RADIUS,
                    np.linalg.norm(midpoints[:, :2], axis=1).min() - BOND_RADIUS)
    assert clearance > 0 and abs(part.BoundingBox().zlen -
                                 ((3 * rows + 1) * PITCH / 2 + 2 * NODE_RADIUS)) < 1e-6
    print(f"{sectors} x {rows}: {len(spheres)} nodes, {len(edges)} bonds, "
          f"{hexagons} hexagons; pitch radius {radii.mean():.3f}, "
          f"height {part.BoundingBox().zlen:.3f}, bonds {lengths.min():.3f}–{lengths.max():.3f}, "
          f"clear axial diameter ≥ {2 * clearance:.3f} mm")


def export(path, sectors, rows):
    cq.exporters.export(lattice(sectors, rows), str(path))
    check(path, sectors, rows)


if __name__ == "__main__":
    export(HERE / "nanotube.step", 7, 8)
    with TemporaryDirectory() as temp:
        export(Path(temp) / "wider.step", 9, 8)
        export(Path(temp) / "longer.step", 7, 10)
