"""
Creates a 1000m x 1000m orthomosaic as COG from the latest Sentinel-2 tiles covering Reckenholz, Switzerland.
"""

import os
from pathlib import Path

import numpy as np
import planetary_computer
import pystac_client
import rasterio
from dotenv import load_dotenv
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject
from rasterio.warp import transform as rio_transform

CENTER = (2_681_389.0, 1_253_653.0)  # Reckenholz, EPSG:2056
LENGTH = 1000.0  # 1000m square
RES = 10  # output pixel size in meters (10 cm native source)
N_PX = int(LENGTH / RES)

load_dotenv()

file_dir = Path(__file__).parent
OUT = file_dir / "output" / "reckenholz_s2.tif"

os.makedirs(OUT.parent, exist_ok=True)

half = LENGTH / 2
t = from_bounds(
    CENTER[0] - half, CENTER[1] - half, CENTER[0] + half, CENTER[1] + half, N_PX, N_PX
)
lon, lat = rio_transform(
    "EPSG:2056",
    "EPSG:4326",
    [CENTER[0] - half, CENTER[0] + half],
    [CENTER[1] - half, CENTER[1] + half],
)
bbox = (min(lon), min(lat), max(lon), max(lat))

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)
item = next(
    iter(
        catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            datetime="2026-01-01/..",
            query={"eo:cloud_cover": {"lt": 20}},
            sortby="-properties.datetime",
        ).items()
    )
)
print(item.id, item.datetime.date(), item.properties["eo:cloud_cover"])

rgb = []
for band in ["B04", "B03", "B02"]:
    with rasterio.open(item.assets[band].href) as src:
        out = np.empty((N_PX, N_PX), dtype="float32")
        reproject(
            rasterio.band(src, 1),
            out,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=t,
            dst_crs="EPSG:2056",
            resampling=Resampling.bilinear,
        )
        rgb.append(out)

rgb = np.stack(rgb) / 10000.0
rgb[rgb == 0.0] = -1.0

with rasterio.open(
    OUT,
    "w",
    driver="COG",
    width=N_PX,
    height=N_PX,
    count=3,
    dtype="float32",
    crs="EPSG:2056",
    transform=t,
    nodata=-1.0,
    compress="DEFLATE",
    overviews=[2, 4],
) as dst:
    dst.write(rgb)
print("wrote", OUT)
