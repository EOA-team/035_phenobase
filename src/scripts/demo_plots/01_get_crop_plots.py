import os 
import psycopg2
import pandas as pd
from psycopg2.extensions import connection
from dotenv import load_dotenv
import geopandas as gpd
from pathlib import Path

load_dotenv()   

file_dir = Path(__file__).parent
OUT_DIR = file_dir / "output" 
OUT_FILE = "crop_plots.geojson"
FIELDS_OF_INTEREST = ["RE_206_Demo1", "RE_206_Demo2", "RE_206_Demo3"] # Demo 



def get_geowp_connection():
    return psycopg2.connect(
        host=os.getenv("GEOWP_HOST"),
        dbname="geo_wp",
        user=os.getenv("GEOWP_USER"),
        password=os.getenv("GEOWP_PASSWORD"),
    )

def list_geowp_tables(conn: connection):
    cur = conn.cursor()
    cur.execute(
        "SELECT table_schema, table_name, table_type "
        "FROM information_schema.tables "
        "WHERE table_schema NOT IN ('pg_catalog', 'information_schema') "
        "ORDER BY table_schema, table_name"
    )
    tables = cur.fetchall()
    cur.close()
    return tables


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = get_geowp_connection()
    schlaege_tbl = "agroscope_versuchsflaechen_2023.versuchsflaeche"
    gdf = gpd.read_postgis(f"SELECT geom FROM {schlaege_tbl} WHERE id_ags IN {tuple(FIELDS_OF_INTEREST)} ", conn)
    gdf = gdf.to_crs("EPSG:2056")
    for plot in range(len(gdf)):
        gdf.loc[plot, "row"] = 1
        gdf.loc[plot, "col"] = plot + 1
        gdf.loc[plot, "id"] = f"x1_y{plot + 1}"
    gdf = gdf.astype({"col": "int64", "row": "int64"})
    out_file = OUT_DIR / OUT_FILE
    gdf.to_file(out_file, driver="GeoJSON")

    conn.close()

