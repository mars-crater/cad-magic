"""Show the saved STEP assembly in a three-quarter and axial view."""
from pathlib import Path

import cadquery as cq
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PAPER = "#f8f6ef"


def mesh():
    xyz, colors = [], []
    part = cq.importers.importStep(str(HERE / "nanotube.step")).val()
    for body in part.Solids():
        verts, faces = body.tessellate(0.04, 0.32)
        triangles = np.array([v.toTuple() for v in verts])[faces]
        xyz.append(triangles)
        color = [207, 144, 66] if len(body.Faces()) == 1 else [49, 118, 125]
        colors.extend([color] * len(triangles))
    return np.concatenate(xyz), np.array(colors)


def project(xyz, colors, view, roll, size):
    view = np.array(view, dtype=float)
    view /= np.linalg.norm(view)
    right = np.cross([0, 1, 0], view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    theta = np.radians(roll)
    right, up = (np.cos(theta) * right + np.sin(theta) * up,
                 np.cos(theta) * up - np.sin(theta) * right)
    projected = xyz @ np.stack([right, -up], axis=1)
    lo, hi = projected.min(axis=(0, 1)), projected.max(axis=(0, 1))
    pixels = (projected - (lo + hi) / 2) * min((np.array(size) - 40) / (hi - lo)) + np.array(size) / 2
    normals = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-9)
    light = 0.5 * up - 0.4 * right + 0.72 * view
    depth = xyz.mean(axis=1) @ view
    shading = (0.64 + 0.43 * np.clip(normals @ light, 0, 1))
    shaded = np.minimum(colors * shading[:, None], 255)
    far = (depth.max() - depth) / np.ptp(depth)
    fog = (0.32 * far ** 2)[:, None]
    palette = (shaded * (1 - fog) + 240 * fog).astype(int)
    # A depth buffer keeps back-wall rods behind front-wall joints even when
    # the long faces of two cylinders overlap in screen space.
    frame = np.empty((size[1], size[0], 3), dtype=np.uint8)
    frame[:] = [248, 246, 239]
    buffer = np.full((size[1], size[0]), -np.inf)
    depths = xyz @ view
    for f in np.flatnonzero(normals @ view > 0):
        triangle = pixels[f]
        low = np.maximum(np.floor(triangle.min(axis=0)).astype(int), 0)
        high = np.minimum(np.ceil(triangle.max(axis=0)).astype(int) + 1, size)
        x0, y0 = low
        x1, y1 = high
        if x0 >= x1 or y0 >= y1:
            continue
        a, b, c = triangle
        ab, ac = b - a, c - a
        det = ab[0] * ac[1] - ab[1] * ac[0]
        if abs(det) < 1e-8:
            continue
        y, x = np.ogrid[y0:y1, x0:x1]
        dx, dy = x + 0.5 - a[0], y + 0.5 - a[1]
        u = (dx * ac[1] - dy * ac[0]) / det
        v = (ab[0] * dy - ab[1] * dx) / det
        za, zb, zc = depths[f]
        z = za + u * (zb - za) + v * (zc - za)
        region = buffer[y0:y1, x0:x1]
        keep = (u >= 0) & (v >= 0) & (u + v <= 1) & (z > region)
        region[keep] = z[keep]
        frame[y0:y1, x0:x1][keep] = palette[f]
    return Image.fromarray(frame)


if __name__ == "__main__":
    triangles, colors = mesh()
    page = Image.new("RGB", (2000, 820), PAPER)
    page.paste(project(triangles, colors, (-1, 0.1, 0.61), -24, (1370, 790)), (12, 15))
    page.paste(project(triangles, colors, (0, 0, 1), 0, (555, 550)), (1410, 135))
    page.resize((1200, 492), Image.Resampling.LANCZOS).save(HERE / "nanotube.png")
