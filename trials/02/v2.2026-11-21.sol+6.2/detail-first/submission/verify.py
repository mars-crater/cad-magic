"""Verify output STEP solids against the design and the independent SVG artwork."""
from io import BytesIO

import cadquery as cq
import cairosvg
import numpy as np
from PIL import Image, ImageDraw

from build import ANCHOR_HEIGHT, BASE, BORE, OUT, RIM, ROPE_HEIGHT, WIDTH
from build import cylinder, develop, heightmap, prism, xyz


def read_step(stem):
    solid = cq.importers.importStep(str(OUT / f"{stem}.step")).val()
    assert len(solid.Solids()) == 1 and solid.isValid()
    return solid


def check_bore(solid, width, diameter):
    box = solid.BoundingBox()
    assert abs(box.xlen - width) < 1e-4
    assert abs(box.zlen - BASE - ROPE_HEIGHT) < 1e-4
    center = xyz((80, 24), width=width)
    for elevation in (0.05, BASE / 2, BASE - 0.05, BASE + ANCHOR_HEIGHT - 0.1):
        section = cq.Workplane("XY").add(solid).section(elevation).val()
        circular_edges = [edge for edge in section.Edges()
                          if edge.geomType() == "CIRCLE"
                          and abs(edge.Length() - np.pi * diameter) < 1e-5
                          and abs(edge.Center().x - center.x) < 1e-6
                          and abs(edge.Center().y - center.y) < 1e-6]
        assert len(circular_edges) == 1
    gauge = cylinder((80, 24), diameter / 2 - 0.005, -0.1, box.zlen + 0.2, width)
    assert solid.intersect(gauge).Volume() < 1e-6
    wall_height = BASE - 0.1
    collar = cylinder((80, 24), diameter / 2 + 2, 0.05, wall_height, width).cut(gauge)
    expected = np.pi * ((diameter / 2 + 2) ** 2 - (diameter / 2) ** 2) * wall_height
    assert abs(solid.intersect(collar).Volume() - expected) < 1e-5
    print(f"Width {box.xlen:.4f}, height {box.ylen:.4f}, thickness {box.zlen:.4f} mm; "
          f"bore Ø{diameter:.2f} mm centered at ({center.x:.4f}, {center.y:.4f}) mm, "
          "4 circular sections, full-length gauge clear, 2 mm uninterrupted backing collar.")


def compare(solid, coupon):
    sample = 8
    dims = (180 * sample, 160 * sample)
    top_left = xyz((0, 0))
    depth = heightmap(solid, top_left.x, top_left.y, sample * 142 / WIDTH, dims)
    coupon_depth = heightmap(coupon, top_left.x, top_left.y, sample * 142 / WIDTH, dims)
    ref_bytes = cairosvg.svg2png(url=str(OUT.parent / "reference.svg"),
                                output_width=dims[1], output_height=dims[0])
    ref = Image.open(BytesIO(ref_bytes)).convert("RGB")
    pixels = np.array(ref, dtype=int)
    targets = ((39, 57, 71), (152, 100, 56))
    top_planes = (BASE + ANCHOR_HEIGHT, BASE + ROPE_HEIGHT)
    canvas = Image.new("RGB", (3 * 340, 420), (231, 233, 235))
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 9), "SOURCE SVG", fill=(34, 41, 47))
    canvas.paste(ref.resize((320, 360), Image.Resampling.LANCZOS), (10, 42))
    draw.text((358, 9), "REOPENED STEP / RELIEF MASKS", fill=(34, 41, 47))
    diagnostic = np.full((*dims, 3), 255, dtype=np.uint8)
    overlay = diagnostic.copy()
    roi = np.s_[44*sample:101*sample, 46*sample:124*sample]
    for name, target, plane in zip(("anchor", "rope"), targets, top_planes):
        expected = np.linalg.norm(pixels - target, axis=2) < 65
        actual = np.isclose(depth, plane)
        coupon_actual = np.isclose(coupon_depth, plane)
        iou = np.count_nonzero(actual & expected) / np.count_nonzero(actual | expected)
        coupon_iou = np.count_nonzero((coupon_actual & expected)[roi]) / np.count_nonzero(
            (coupon_actual | expected)[roi])
        assert iou > 0.93 and coupon_iou > 0.93
        print(f"{name}: SVG vs STEP top footprint IoU {iou:.2%}; coupon interior IoU {coupon_iou:.2%}")
        diagnostic[actual] = target
        overlay[actual & expected] = (112, 120, 122)
        overlay[expected & ~actual] = (223, 111, 51)
        overlay[actual & ~expected] = (33, 150, 173)
    canvas.paste(Image.fromarray(diagnostic).resize((320, 360), Image.Resampling.LANCZOS), (350, 42))
    draw.text((698, 9), "AGREEMENT / EDGE DIFFERENCES", fill=(34, 41, 47))
    draw.text((698, 25), "Gray both | Orange SVG only | Blue CAD only", fill=(34, 41, 47))
    canvas.paste(Image.fromarray(overlay).resize((320, 360), Image.Resampling.LANCZOS), (690, 42))
    canvas.save(OUT / "comparison.png")


def check_crossing(solid, label):
    y = np.arange(73, 91.01, 0.05)
    labels = []
    for v in y:
        upper = solid.isInside(xyz((80, v), BASE + 1.05))
        lower = solid.isInside(xyz((80, v), BASE + 0.4))
        labels.append("R" if upper else "A" if lower else "-")
    starts = [0] + [i for i in range(1, len(labels)) if labels[i] != labels[i - 1]]
    pattern = "".join(labels[i] for i in starts)
    assert pattern == "A-R-A", (pattern, y[starts])
    gaps = [(y[starts[i + 1]] - y[starts[i]]) * WIDTH / 142 for i in (1, 3)]
    assert min(gaps) > 0.9
    print(f"{label} crossing at stem center: {pattern}; sampled axial gaps "
          f"{gaps[0]:.2f} and {gaps[1]:.2f} mm.")


if __name__ == "__main__":
    coupon = read_step("coupon")
    assert abs(coupon.BoundingBox().xlen - 82 * WIDTH / 142) < 1e-4
    assert abs(coupon.BoundingBox().zlen - BASE - ROPE_HEIGHT) < 1e-4
    check_crossing(coupon, "Reopened coupon")
    final = read_step("final")
    check_crossing(final, "Reopened final")
    check_bore(final, WIDTH, BORE)
    outer_prism = prism([cq.Edge.makeBezier([xyz(p) for p in segment]) for segment in RIM],
                        BASE + ROPE_HEIGHT + 0.1)
    outside = final.cut(outer_prism).Volume()
    assert outside < 1e-5
    print(f"Volume outside backing footprint: {outside:.8f} mm³.")
    compare(final, coupon)
    print("Parameter edit (unexported rebuild):")
    variant = develop(False, width=66, bore=7.0)
    assert len(variant.Solids()) == 1 and variant.isValid()
    check_bore(variant, 66, 7.0)
