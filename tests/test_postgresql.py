"""Tests to verify that the PostgreSQL database with PostGIS Extension
is accessible and functioning correctly.
"""

import pytest
from sqlalchemy import text

from src.db import get_engine_postgresql
from src.settings import Infrastructure, Settings

EXPECTED_VERSIONS = {
    Infrastructure.LOCAL: {"postgres": "PostgreSQL 16.4", "postgis": "3.4"},
    Infrastructure.AGS_FOLA: {"postgres": "PostgreSQL 16.15", "postgis": "3.4"},
}

_infra = Settings().infrastructure


@pytest.fixture(name="phenobase", scope="function")
def phenobase_conn():
    """PostgreSQL connection fixture.
    The connection is established before each test and closed after the test."""
    engine = get_engine_postgresql()
    with engine.connect() as conn:
        yield conn
    engine.dispose()


@pytest.mark.integration
@pytest.mark.parametrize("expected_dbs", ["test_phenobase"])
def test_available_databases(phenobase, expected_dbs):
    """Check that expected databases are available on the PostgreSQL server"""
    query = text("SELECT datname FROM pg_database;")
    result = phenobase.execute(query).fetchall()
    available_dbs = [row[0] for row in result]
    assert expected_dbs in available_dbs


@pytest.mark.integration
@pytest.mark.parametrize("expected_version", [EXPECTED_VERSIONS[_infra]["postgres"]])
def test_postgres_version(phenobase, expected_version):
    """Check expected PostgreSQL version is installed on the server"""
    query = text("SELECT version();")
    result = phenobase.execute(query).scalar()
    assert expected_version in result


@pytest.mark.integration
@pytest.mark.parametrize("expected_ext", ["postgis", "plpgsql"])
def test_available_extensions(phenobase, expected_ext):
    """Check that expected extensions are available on the Database"""
    query = text(
        "SELECT name, default_version, comment FROM pg_available_extensions ORDER BY name"
    )
    result = phenobase.execute(query).fetchall()
    available_ext = [row[0] for row in result]
    assert expected_ext in available_ext


@pytest.mark.integration
@pytest.mark.parametrize("expected_version", [EXPECTED_VERSIONS[_infra]["postgis"]])
def test_postgis_version(phenobase, expected_version):
    """Check that PostGIS extension is installed and has the expected version"""
    query = text("SELECT PostGIS_Version();")
    result = phenobase.execute(query).scalar()
    assert expected_version in result


@pytest.mark.integration
def test_postgis_crud(phenobase):
    """C=Create, R=Read, U=Update, D=Delete — full crud with geometry."""
    # C: Create a temporary table and insert 3 polygons
    phenobase.execute(
        text("""
        CREATE TEMP TABLE test_geom (
            id   SERIAL,
            geom GEOMETRY(Polygon, 4326)
        )
    """)
    )
    phenobase.execute(
        text("""
        INSERT INTO test_geom (geom) VALUES
            (ST_MakeEnvelope(-10, -10, 10, 10, 4326)),
            (ST_MakeEnvelope( -5,  -5,  5,  5, 4326)),
            (ST_MakeEnvelope( -1,  -1,  1,  1, 4326))
    """)
    )

    # R: Read the inserted polygon and check its (idx,area)
    rows = phenobase.execute(text("SELECT id, ST_Area(geom) FROM test_geom")).fetchall()
    assert len(rows) == 3
    assert rows[0] == (1, 400.0)
    assert rows[1] == (2, 100.0)
    assert rows[2] == (3, 4.0)

    # U : Update polygon with ID=2
    phenobase.execute(
        text("""
        UPDATE test_geom
        SET geom = ST_MakeEnvelope(-2, -2, 2, 2, 4326)
        WHERE id = 2
    """)
    )
    rows = phenobase.execute(
        text("SELECT id, ST_Area(geom) FROM test_geom ORDER BY id")
    ).fetchall()
    assert rows[1] == (2, 16.0)

    # R: Read Spatial Relationships
    # ST_Within(geom, box) is true when geom is fully inside the query box
    results = phenobase.execute(
        text("""
        SELECT id, ST_Within(geom, ST_MakeEnvelope(-6, -6, 6, 6, 4326))
        FROM test_geom
        ORDER BY id
    """)
    )
    results = results.fetchall()
    assert results[0] == (1, False), "id=1 is too large for the box"
    assert results[1] == (2, True), "id=2 fits inside"
    assert results[2] == (3, True), "id=3 fits inside"

    # D : Delete ID=1 and check that only 2 rows remain
    phenobase.execute(text("DELETE FROM test_geom WHERE id = 1"))
    assert phenobase.execute(text("SELECT count(*) FROM test_geom")).fetchone()[0] == 2
