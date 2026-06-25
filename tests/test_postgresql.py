""" Tests to verify that the PostgreSQL database with PostGIS Extension
 is accessible and functioning correctly.
"""

import pytest
from dotenv import load_dotenv
from src.postgresql_helper import connect_to_database

load_dotenv()  # Load environment variables from .env file

@pytest.fixture(name="phenobase")
def phenobase_conn():
    """PostgreSQL connection to database with the name phenobase"""
    conn = connect_to_database(dbname="phenobase")
    yield conn
    conn.close()

@pytest.mark.integration_test
@pytest.mark.parametrize("version", ["PostgreSQL 16.14"])
def test_postgres_version(phenobase, version):
    """ Check expected PostgreSQL version is installed on the server """
    cur = phenobase.cursor()
    cur.execute("SELECT version();")
    result = cur.fetchone()[0]
    cur.close()
    assert version in result

@pytest.mark.integration_test
@pytest.mark.parametrize("expected_ext", ["postgis", "plpgsql"])
def test_available_extensions(phenobase, expected_ext):
    """ Check that expected extensions are available on the Database"""
    cur = phenobase.cursor()
    cur.execute(
        "SELECT name, default_version, comment FROM pg_available_extensions ORDER BY name")
    available_ext = [row[0] for row in cur.fetchall()]
    cur.close()
    assert expected_ext in available_ext

@pytest.mark.integration_test
@pytest.mark.parametrize("version", ["3.4"])
def test_postgis_version(phenobase, version):
    """ Check that PostGIS extension is installed and has the expected version"""
    cur = phenobase.cursor()
    cur.execute("SELECT PostGIS_Version();")
    result = cur.fetchone()[0]
    assert version in result
    cur.close()

@pytest.mark.integration_test
@pytest.mark.parametrize("expected_dbs", ["phenobase"])
def test_available_databases(phenobase, expected_dbs):
    """ Check that expected databases are available on the PostgreSQL server """
    cur = phenobase.cursor()
    cur.execute("SELECT datname FROM pg_database;")
    result = cur.fetchall()
    available_dbs = [row[0] for row in result]
    assert expected_dbs in available_dbs
    cur.close()

@pytest.mark.integration_test
def test_postgis_crud(phenobase):
    """C=Create, R=Read, U=Update, D=Delete — full crud with geometry."""
    cur = phenobase.cursor()

    # C :Create temp table and insert 3 polygons
    cur.execute("""
        CREATE TEMP TABLE test_geom (
            id   SERIAL,
            geom GEOMETRY(Polygon, 4326)
        )
    """)
    cur.execute("""
        INSERT INTO test_geom (geom) VALUES
            (ST_MakeEnvelope(-10, -10, 10, 10, 4326)),
            (ST_MakeEnvelope( -5,  -5,  5,  5, 4326)),
            (ST_MakeEnvelope( -1,  -1,  1,  1, 4326))
    """)

    # R: Read the inserted polygon and check its (idx,area)
    cur.execute("SELECT id, ST_Area(geom) FROM test_geom")
    rows = cur.fetchall()
    assert len(rows) == 3
    assert rows[0] == (1, 400.0)
    assert rows[1] == (2, 100.0)
    assert rows[2] == (3,   4.0)

    # U : Update polygon with ID=2
    cur.execute("""
        UPDATE test_geom
        SET geom = ST_MakeEnvelope(-2, -2, 2, 2, 4326)
        WHERE id = 2
    """)

    cur.execute("SELECT id, ST_Area(geom) FROM test_geom ORDER BY id")
    rows = cur.fetchall()
    assert rows[1] == (2, 16.0)

    # R: Read Spatial Relationships
    # ST_Within(geom, box) is true when geom is fully inside the query box
    cur.execute("""
        SELECT id, ST_Within(geom, ST_MakeEnvelope(-6, -6, 6, 6, 4326))
        FROM test_geom
        ORDER BY id
    """)
    results = cur.fetchall()
    assert results[0] == (1, False), "id=1 is too large for the box"
    assert results[1] == (2, True),  "id=2 fits inside"
    assert results[2] == (3, True),  "id=3 fits inside"

    # D : Delete ID=1 and check that only 2 rows remain
    cur.execute("DELETE FROM test_geom WHERE id = 1")
    cur.execute("SELECT count(*) FROM test_geom")
    assert cur.fetchone()[0] == 2

    cur.close()
