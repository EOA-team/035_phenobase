
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import os
from dotenv import load_dotenv

load_dotenv()  

base_url = URL.create(
    "postgresql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
)

# 0. See Privileges of DB User
engine = create_engine(base_url.set(database="db1"))
with engine.connect() as conn:
    result = conn.execute(text("SELECT current_user, session_user;"))
    print(result.fetchone())

    # Check CREATEDB and superuser privileges
    result = conn.execute(text("""
        SELECT rolname, rolcreatedb, rolsuper, rolcreaterole
        FROM pg_roles WHERE rolname = current_user;
    """))
    row = result.fetchone()
    print(f"User: {row[0]}, CREATEDB: {row[1]}, SUPERUSER: {row[2]}")

    # Alternative quick check
    result = conn.execute(text("SHOW is_superuser;"))
    print(f"is_superuser: {result.fetchone()[0]}")   

# 1. Connect to 'postgres' to create DB
engine = create_engine(
    base_url.set(database="postgres"), 
    isolation_level="AUTOCOMMIT")
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'phenobase'"))
    if not result.fetchone():
        conn.execute(text("CREATE DATABASE phenobase"))

# 2. Connect to 'phenobase' to install PostGIS
engine = create_engine(base_url.set(database="db1"))
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    result = conn.execute(text("SELECT PostGIS_Version()"))
    print(result.scalar())


# import psycopg2
# import os 
# from dotenv import load_dotenv

# load_dotenv()  # Load environment variables from .env file

# # Helper Functions for PostgreSQL Database Operations
# def connect_to_database(db:str) -> psycopg2.connection:
#     conn = psycopg2.connect(
#         dbname=db,
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD"),
#         host=os.getenv("DB_HOST"),
#         port=os.getenv("DB_PORT")
#         )
#     return conn

# def check_db_exists(conn: psycopg2.connection, db: str) -> bool:
#     """Checks if a database exists in the PostgreSQL server"""
#     cur = conn.cursor()
#     cur.execute("SELECT 1 FROM pg_database WHERE datname=%s;", (db,))
#     exists = cur.fetchone() is not None
#     return exists


# def initialize_phenobase():
#     create_db(new_db="phenobase")
#     install_postgis(target_db="phenobase")

    


# def create_db(new_db:str):
#     """Creates PostgreSQL database """
#     maintenance_db= "postgres" # Default Maintenance DB 
#     conn =connect_to_database(maintenance_db)  
#     if check_db_exists(conn, new_db):
#         print(f"Database '{new_db}' already exists.")
        
#     else:
#         conn.set_session(autocommit=True)  # Enable autocommit mode for database creation
#         cur = conn.cursor()
#         cur.execute(f"CREATE DATABASE {new_db};")
#         print(f"Database '{new_db}' created successfully.")
#         cur.close()
    
#     conn.close()
        
        

# def install_postgis(target_db:str):
#     """Installs PostGIS extension in the specified database"""
#     conn = connect_to_database(target_db)
#     cur = conn.cursor()
#     cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
#     conn.commit()
#     cur.execute("SELECT PostGIS_Version();")
#     postgis_version = cur.fetchone()[0]
#     print(f"Installed PostGIS version: {postgis_version}")
#     cur.close()
#     conn.close()


# if __name__ == "__main__":
#     initialize_phenobase()