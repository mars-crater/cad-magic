"""Render imported STEP with a fixed orthographic camera and compare side silhouette."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_erosion

from banana import DATUM, MM_PER_PIXEL, read_step, verify

SIZE = 488
AA = 2
LIGHT = np.array([-0.44, 0.66, 0.61])
LIGHT /= np.linalg.norm(LIGHT)


def raster(step, view_degrees=0):
    part = read_step(step)
    angle = np.deg2rad(view_degrees)
    depth_buffer = np.full((SIZE * AA, SIZE * AA), -np.inf)
    rgb = np.full((*depth_buffer.shape, 3), 255, dtype=np.uint8)
    for face in part.Faces():
        nodes, triangles = face.tessellate(0.055, 0.12)
        points = np.array([node.toTuple() for node in nodes])
        points[:, [1, 2]] = points[:, [1, 2]] @ [
            [np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]]
        index = np.asarray(triangles)
        a, b, c = points[index].transpose(1, 0, 2)
        normals = np.cross(b-a, c-a)
        smooth = np.zeros_like(points)
        for corner in index.T:
            np.add.at(smooth, corner, normals)
        smooth /= np.maximum(np.linalg.norm(smooth, axis=1, keepdims=True), 1e-12)
        projected = np.column_stack((points[:, 0] / MM_PER_PIXEL + DATUM[0],
                                     DATUM[1] - points[:, 1] / MM_PER_PIXEL)) * AA
        for tri in index:
            p, q, r = projected[tri]
            u, v = q-p, r-p
            determinant = u[0]*v[1] - u[1]*v[0]
            if abs(determinant) < 1e-8:
                continue
            lo = np.maximum(np.floor(np.min([p, q, r], axis=0)).astype(int), 0)
            hi = np.minimum(np.ceil(np.max([p, q, r], axis=0)).astype(int)+1, SIZE*AA)
            xx, yy = np.meshgrid(np.arange(lo[0], hi[0])+0.5,
                                 np.arange(lo[1], hi[1])+0.5)
            wb = ((xx-p[0])*v[1] - (yy-p[1])*v[0])/determinant
            wc = (u[0]*(yy-p[1]) - u[1]*(xx-p[0]))/determinant
            wa = 1-wb-wc
            dep = points[tri, 2]
            z = dep[0]*wa + dep[1]*wb + dep[2]*wc
            zone = np.s_[lo[1]:hi[1], lo[0]:hi[0]]
            update = (wa >= -1e-8) & (wb >= -1e-8) & (wc >= -1e-8) & (z > depth_buffer[zone])
            if not update.any():
                continue
            weights = np.stack([wa[update], wb[update], wc[update]], axis=1)
            n = weights @ smooth[tri]
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
            x, y = (weights @ points[tri])[:, :2].T
            peel = np.tile([245, 198, 38.], (len(x), 1))
            stem = np.clip((y+32)/22, 0, 1)
            peel = peel*(1-stem[:, None]) + np.array([161, 150, 60])*stem[:, None]
            tip = np.clip((x-163)/6, 0, 1)
            peel = peel*(1-tip[:, None]) + np.array([132, 107, 37])*tip[:, None]
            if face.geomType() == 'PLANE':
                peel[:] = [131, 101, 54]
            illumination = 0.57 + 0.52*np.maximum(n @ LIGHT, 0)
            rgb[zone][update] = np.clip(peel * illumination[:, None], 0, 255).astype(np.uint8)
            depth_buffer[zone][update] = z[update]
    mask = np.isfinite(depth_buffer).reshape(SIZE, AA, SIZE, AA).mean((1, 3)) >= 0.5
    picture = Image.fromarray(rgb).resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    return picture, mask


if __name__ == '__main__':
    standard, mask = raster('banana.step')
    standard.save('banana-matched.png')
    angle, _ = raster('banana.step', 30)
    angle.save('banana-oblique.png')
    deep, deep_mask = raster('banana-deeper.step')
    deep.save('banana-deeper-matched.png')
    comparison = Image.new('RGB', (SIZE*3, SIZE+34), '#f6f6f6')
    reference = Image.open('Banana.jpg')
    comparison.paste(reference, (0, 34))
    comparison.paste(standard, (SIZE, 34))
    overlay = np.array(reference.convert('RGB'))
    photo_mask = np.array(Image.open('reference-mask.png')) > 128
    overlay[photo_mask & ~binary_erosion(photo_mask, iterations=2)] = [10, 110, 230]
    overlay[mask & ~binary_erosion(mask, iterations=1)] = [230, 34, 105]
    comparison.paste(Image.fromarray(overlay), (2*SIZE, 34))
    labels = ('Reference photo', 'Reimported STEP, matched side view',
              'Edge overlay: photo (blue) / STEP (magenta)')
    for i, label in enumerate(labels):
        ImageDraw.Draw(comparison).text((i*SIZE+12, 11), label, fill='#141414')
    comparison.save('banana-comparison.png')
    def iou(a,b):
        return (a&b).sum()/(a|b).sum()
    print(f'Silhouette IoU: reference to STEP = {iou(photo_mask, mask):.4f}; '
          f'edited depth to default = {iou(mask, deep_mask):.4f}')
    for name, data in [('photo mask', photo_mask), ('STEP silhouette', mask)]:
        y, x = np.nonzero(data)
        print(f'{name} extrema, pixels: x={x.min()}…{x.max()}, y={y.min()}…{y.max()}')
    original = verify(read_step(Path('banana.step')))
    edited = verify(read_step(Path('banana-deeper.step')))
    assert iou(mask, deep_mask) > .997
    assert np.allclose(original[:2], edited[:2], atol=0.002)
    assert np.isclose(edited[2]/original[2], .92/.77, rtol=0.0005)
    print(f'Edited / original depth = {edited[2]/original[2]:.5f}; requested ratio = {.92/.77:.5f}')
