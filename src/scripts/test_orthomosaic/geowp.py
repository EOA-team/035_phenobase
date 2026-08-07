import os 
import psycopg2
import pandas as pd
from psycopg2.extensions import connection
from dotenv import load_dotenv
import geopandas as gpd
from pathlib import Path

load_dotenv()   

file_dir = Path(__file__).parent
OUT = file_dir / "output" / "experiment_plot.geojson"

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
    conn = get_geowp_connection()
    schlaege_tbl = "agroscope_versuchsflaechen_2023.versuchsflaeche"
    gdf =  gpd.read_postgis(f"SELECT * FROM {schlaege_tbl} WHERE id_ags = 'RE_112O' ", conn)
    gdf = gdf.to_crs("EPSG:2056")
    gdf.to_file(OUT, driver="GeoJSON")

    conn.close()
