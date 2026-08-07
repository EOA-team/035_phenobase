import os 
import psycopg2
from dotenv import load_dotenv

load_dotenv()   

def get_geowp_connection():
    return psycopg2.connect(
        host=os.getenv("GEOWP_HOST"),
        dbname="geo_wp",
        user=os.getenv("GEOWP_USER"),
        password=os.getenv("GEOWP_PASSWORD"),
    )


conn = get_geowp_connection()
cur = conn.cursor()
cur.execute(
    "SELECT table_schema, table_name, table_type "
    "FROM information_schema.tables "
    "WHERE table_schema NOT IN ('pg_catalog', 'information_schema') "
    "ORDER BY table_schema, table_name"
)
for schema, name, t in cur.fetchall():
    print(f"{schema}.{name} ({t})")
cur.close()
conn.close()
