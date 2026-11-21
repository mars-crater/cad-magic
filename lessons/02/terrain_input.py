"""Optional refresh of the small, north-up Hawaiʻi Island DEM crop from Mapzen."""
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ZOOM = 8
# Global Web Mercator pixel of the crop's upper left edge (east and south positive).
LEFT, TOP, WIDTH, HEIGHT = 4340, 28989, 266, 294


def fetch():
    mosaic = Image.new("RGB", (512, 512))
    for x in (16, 17):
        for y in (113, 114):
            url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{ZOOM}/{x}/{y}.png"
            with urlopen(url, timeout=30) as response:
                tile = Image.open(BytesIO(response.read())).convert("RGB")
            mosaic.paste(tile, ((x - 16) * 256, (y - 113) * 256))
    x = LEFT - 16 * 256
    y = TOP - 113 * 256
    rgb = np.asarray(mosaic.crop((x, y, x + WIDTH, y + HEIGHT))).astype(float)
    meters = rgb[:, :, 0] * 256 + rgb[:, :, 1] + rgb[:, :, 2] / 256 - 32768
    Image.fromarray(np.maximum(0, meters).round().astype("uint16")).save(HERE / "terrain-dem.png")


if __name__ == "__main__":
    fetch()
