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



