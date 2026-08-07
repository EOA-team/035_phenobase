import sys
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon
from pathlib import Path

file_dir = Path(__file__).parent
IN_DIR = file_dir / "output"
IN_FILE = "experiment_plot.geojson"
OUT_FILE = "crop_plots.geojson"

GRID_X = 1
GRID_Y = 5


def load_polygon(path=None):
    if path:
        return gpd.read_file(path)
    return gpd.read_file(IN_DIR / IN_FILE)


def make_grid(gdf, rows=GRID_Y, cols=GRID_X):
    gdf = gdf.to_crs(2056)
    xmin, ymin, xmax, ymax = gdf.total_bounds
    xs = np.linspace(xmin, xmax, cols + 1)
    ys = np.linspace(ymin, ymax, rows + 1)

    cells, rows_list, cols_list, ids = [], [], [], []
    for r in range(rows):
        for c in range(cols):
            cells.append(Polygon([
                (xs[c], ys[r]), (xs[c + 1], ys[r]),
                (xs[c + 1], ys[r + 1]), (xs[c], ys[r + 1]),
            ]))
            rows_list.append(r + 1)
            cols_list.append(c + 1)
            ids.append(f"x{c + 1}_y{r + 1}")

    return gpd.GeoDataFrame(
        {"row": rows_list, "col": cols_list, "id": ids, "geometry": cells},
        crs=2056,
    )


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    out = sys.argv[2] if len(sys.argv) > 2 else str(file_dir / "output" / OUT_FILE)
    polygon = load_polygon(path)
    grid = make_grid(polygon)
    print(f"Created {len(grid)} polygons")
    print(grid[["id", "row", "col"]].head())
    grid.to_file(out)
    print(f"Saved to {out}")
