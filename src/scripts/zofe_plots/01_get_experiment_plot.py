import os 
import psycopg
import pandas as pd
from dotenv import load_dotenv
import geopandas as gpd
from pathlib import Path

load_dotenv()   

file_dir = Path(__file__).parent
OUT_DIR = file_dir / "output" 
OUT_FILE = "experiment_plot.geojson"
FIELDS_OF_INTEREST = 'RE_215' # ZOFE Experiment Plot 



def get_geowp_connection()-> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("GEOWP_HOST"),
        dbname="geo_wp",
        user=os.getenv("GEOWP_USER"),
        password=os.getenv("GEOWP_PASSWORD"),
    )

def list_geowp_tables(conn: psycopg.Connection):
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
    gdf = gpd.read_postgis(f"SELECT geom FROM {schlaege_tbl} WHERE id_ags = '{FIELDS_OF_INTEREST}' ", conn)
    conn.close()

    gdf = gdf.explode(index_parts=False).reset_index(drop=True)  # MultiPolygon -> Polygon
    assert len(gdf) == 1, f"Expected 1 polygon, got {len(gdf)}"
    assert (gdf.geom_type == "Polygon").all()


    gdf = gdf.to_crs("EPSG:2056")
    out_file = OUT_DIR / OUT_FILE
    gdf.to_file(out_file, driver="GeoJSON")
