"""Compare source media with independently reimported STEP geometry."""
from pathlib import Path

import cadquery as cq
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
PAPER = "#fbfaf6"
INK = "#193037"


def font(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def render_part(name, size):
    solid = cq.importers.importStep(str(HERE / f"{name}.step")).val()
    vertices, triangles = solid.tessellate(0.035)
    xyz = np.array([v.toTuple() for v in vertices])
    # Looking down from the south preserves east/right and north/up.
    view = np.array([0., -0.45, 1.])
    view /= np.linalg.norm(view)
    right = np.array([1., 0., 0.])
    coords = xyz @ np.stack([right, np.cross(view, right), view], axis=1)
    xy = coords[:, :2]
    extent = np.ptp(xy, axis=0)
    xy = (xy - (xy.max(axis=0) + xy.min(axis=0)) / 2) * min((size - 40) / extent)
    xy = xy * [1, -1] + size / 2
    faces = np.array(triangles)
    a, b, c = xyz[faces].transpose(1, 0, 2)
    normals = np.cross(b - a, c - a)
    lengths = np.linalg.norm(normals, axis=1)
    normals /= np.maximum(lengths[:, None], 1e-15)
    shade = .60 + .40 * np.clip(normals @ np.array([-.48, -.44, .75]), 0, 1)
    height = xyz[:, 2]
    levels = (height[faces].mean(axis=1) - height.min()) / np.ptp(height)
    if name == "terrain":
        stops = np.array([[34,101,91],[98,152,97],[197,183,122],[154,108,84],[242,230,198]])
    else:
        stops = np.array([[54,79,92],[82,109,119],[226,173,83]])
    colors = np.stack([np.interp(levels, np.linspace(0,1,len(stops)), channel)
                       for channel in stops.T], axis=1) * shade[:, None]
    tile = Image.new("RGB", (size, size), PAPER)
    draw = ImageDraw.Draw(tile)
    for f in np.argsort(coords[faces, 2].mean(axis=1)):
        if normals[f] @ view > 0:
            draw.polygon([tuple(v) for v in xy[faces[f]]], fill=tuple(colors[f].astype(int)))
    return tile


def comparison(rows):
    page = Image.new("RGB", (1140, 1190), PAPER)
    pen = ImageDraw.Draw(page)
    for x, label in [(40, "SOURCE REFERENCE"), (605, "EXPORTED STEP")]:
        pen.text((x, 20), label, fill=INK, font=font(21))
    for i, (name, reference, title) in enumerate(rows):
        y = 80 + i * 550
        pen.line((40, y-12, 1100, y-12), fill="#bdc9c6", width=2)
        pen.text((40, y), title, fill=INK, font=font(29))
        source = Image.open(HERE / reference).convert("RGBA")
        backdrop = Image.new("RGBA", source.size, PAPER)
        backdrop.alpha_composite(source)
        source = ImageOps.contain(backdrop.convert("RGB"), (490, 465))
        page.paste(source, (295-source.width//2, y+275-source.height//2))
        page.paste(render_part(name, 490), (595, y+40))
    page.save(HERE / "renders.png")


if __name__ == "__main__":
    comparison([
        ("terrain", "terrain-reference.png", "Hawaiʻi Island · stepped relief"),
        ("keychain", "keychain-reference.png", "Whale watching · emblem keychain"),
    ])
