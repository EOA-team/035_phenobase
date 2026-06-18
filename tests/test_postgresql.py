""" Tests to verify that the PostgreSQL database is accessible and functioning correctly.
These tests check the database version, available databases, PostGIS extension, and basic insert/query operations"""

import psycopg2
import pytest
import os 
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

@pytest.fixture
def db1_connect():
    """PostgreSQL connection to db1, which is a test database provided by IT
    Opens connection before every test and closes it after test is done."""
    conn = psycopg2.connect(
        dbname="db1", 
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
       )
    yield conn
    conn.close()

@pytest.mark.parametrize("version", ["PostgreSQL 16.14"])
def test_postgres_version(db1_connect, version):
    """ Check connection to PostgreSQL Server by verifying version """
    cur = db1_connect.cursor()
    cur.execute("SELECT version();")
    result = cur.fetchone()[0]
    print(f"PostgreSQL version: {result}")
    assert version in result
    cur.close()

@pytest.mark.parametrize("expected_ext", [
         "plpgsql",
         "postgis"
     ])
def test_installed_extensions(db1_connect, expected_ext):
    """ Check that expected extensions are installed in the database """
    cur = db1_connect.cursor()
    cur.execute("SELECT extname FROM pg_extension")
    installed_ext = [row[0] for row in cur.fetchall()]
    print(f"Installed extensions: {installed_ext}")
    cur.close()
    assert expected_ext in installed_ext

def test_postgis_version(db1_connect):
    cur = db1_connect.cursor()
    cur.execute("SELECT extname FROM pg_extension WHERE extname = 'postgis'")
    if not cur.fetchone():
        pytest.skip("PostGIS not installed")
    cur.execute("SELECT PostGIS_Version();")
    result = cur.fetchone()[0]
    print(f"PostGIS version: {result}")
    assert result != ""
    cur.close()

@pytest.mark.parametrize("expected_dbs", [
         "postgres","mydb","template1",
         "template0","db1"
     ])
def test_available_databases(db1_connect, expected_dbs):
    """ Check that expected databases are available in the PostgreSQL server """
    cur = db1_connect.cursor()
    cur.execute("SELECT datname FROM pg_database;")
    result = cur.fetchall()
    available_dbs = [row[0] for row in result]
    print(f"Available databases: {available_dbs}")
    assert expected_dbs in available_dbs
    cur.close()

def test_insert_and_query(db1_connect):
    """ Test inserting and querying data in a temporary table """
    cur = db1_connect.cursor()
    cur.execute("CREATE TEMP TABLE items (id SERIAL PRIMARY KEY, value TEXT, created_at TIMESTAMPTZ DEFAULT NOW())")
    data = [f"item_{i}" for i in range(10)]
    for val in data:
        cur.execute("INSERT INTO items (value) VALUES (%s)", (val,))
    cur.execute("SELECT value FROM items ORDER BY id")
    results = [row[0] for row in cur.fetchall()]
    print(f"Retrieved values: {results}")
    assert results == data
    cur.close()






