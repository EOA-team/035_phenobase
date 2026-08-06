from pathlib import Path

import rasterio
import requests
from rasterio.merge import merge
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, transform as rio_transform

CENTER = (2_681_389.0, 1_253_653.0)  # Reckenholz, EPSG:2056
LENGTH = 1000.0
RES = 0.1  # output pixel size in meters (10 cm native source)
N_PX = int(LENGTH / RES)

file_dir = Path(__file__).parent
OUT = file_dir / "reckenholz_swissimage.tif"

half = LENGTH / 2
lon, lat = rio_transform(
    "EPSG:2056",
    "EPSG:4326",
    [CENTER[0] - half, CENTER[0] + half],
    [CENTER[1] - half, CENTER[1] + half],
)
bbox = (min(lon), min(lat), max(lon), max(lat))

r = requests.get("https://data.geo.admin.ch/api/stac/v0.9/search", params={
    "collections": "ch.swisstopo.swissimage-dop10",
    "bbox": ",".join(map(str, bbox)),
    "limit": 100,
})
r.raise_for_status()

by_tile = {}
for it in r.json()["features"]:
    tid = it["id"].rsplit("_", 2)[-1]
    year = it["properties"]["datetime"][:4]
    if tid not in by_tile or year > by_tile[tid][0]:
        by_tile[tid] = (year, it)

hrefs = [
    next(v["href"] for k, v in it["assets"].items() if k.endswith("_0.1_2056.tif"))
    for _, (year, it) in by_tile.items()
]

srcs = [rasterio.open(h) for h in hrefs]
mosaic, _ = merge(
    srcs,
    bounds=(CENTER[0] - half, CENTER[1] - half, CENTER[0] + half, CENTER[1] + half),
    res=RES,
    resampling=Resampling.average,
)
for src in srcs:
    src.close()

t = from_bounds(
    CENTER[0] - half, CENTER[1] - half, CENTER[0] + half, CENTER[1] + half, N_PX, N_PX
)
with rasterio.open(
    OUT,
    "w",
    driver="COG",
    width=N_PX,
    height=N_PX,
    count=3,
    dtype=mosaic.dtype,
    crs="EPSG:2056",
    transform=t,
    compress="DEFLATE",
    overviews=[2, 4],
) as dst:
    dst.write(mosaic)
print("wrote", OUT)