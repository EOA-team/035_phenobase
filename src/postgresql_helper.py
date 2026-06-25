"""PostgreSQL helper functions currently support:
- create new database
- install PostGIS extension"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, connection
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


def connect_to_database(dbname: str = "db1") -> connection:
    """Connect to a PostgreSQL database ,
    By Default connects to "db1" which is a test database provided by IT"""
    conn = psycopg2.connect(
        dbname=dbname,
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    return conn


def create_database(dbname: str):
    """Create database if it doesn't exist. 
    Returns True if created, False if already existed."""
    # Connecto to existing db1 as starting point for creating new database
    conn = connect_to_database(dbname="db1")
    # Enable autocommit mode for database creation
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    # Chek if database already exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
    exists = cur.fetchone() is not None
    if not exists:
        cur.execute(f"CREATE DATABASE {dbname};")
        print(f"Database '{dbname}' created successfully.")
        cur.close()
        conn.close()
        return True
    print(f"Database '{dbname}' already exists.")
    cur.close()
    conn.close()
    return False


def install_extension(target_db: str, extension: str):
    """Installs the specified extension in the target database
    Returns True if installed, False if already exists."""
    conn = connect_to_database(target_db)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_extension WHERE extname = %s", (extension,))
    exists = cur.fetchone() is not None
    if not exists:
        cur.execute(f"CREATE EXTENSION IF NOT EXISTS {extension};")
        print(f"Extension '{extension}' installed successfully.")
        cur.close()
        conn.close()
        return True
    print(f"Extension '{extension}' already exists.")
    cur.close()
    conn.close()
    return False


if __name__ == "__main__":
    # Example usage
    create_database("phenobase")
    install_extension("phenobase", "postgis")
