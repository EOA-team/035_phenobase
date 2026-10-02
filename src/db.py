"""Database engine and session management for Phenobase."""

import os
from contextlib import contextmanager
from enum import StrEnum
from functools import cache

from dotenv import load_dotenv
from sqlalchemy import StaticPool, create_engine
from sqlmodel import Session

load_dotenv()


class PhenobaseEnv(StrEnum):
    PRODUCTION = "production"
    TEST = "test"
    TEST_SQLITE = "test_sqlite"
    TEST_DOCKER = "test_docker"


class EngineType(StrEnum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


DB_NAME_LUT = {
    PhenobaseEnv.PRODUCTION: "phenobase",
    PhenobaseEnv.TEST: "test_phenobase",
    PhenobaseEnv.TEST_DOCKER: "test_phenobase",
    # SLite is in-memory, so no database name is needed
}

DB_ENGINE_LUT = {
    PhenobaseEnv.TEST: EngineType.POSTGRESQL,
    PhenobaseEnv.PRODUCTION: EngineType.POSTGRESQL,
    PhenobaseEnv.TEST_SQLITE: EngineType.SQLITE,
    PhenobaseEnv.TEST_DOCKER: EngineType.POSTGRESQL,
}


def get_database_name(phenobase_env: PhenobaseEnv) -> str:
    return DB_NAME_LUT[phenobase_env]


def get_engine_type(phenobase_env: PhenobaseEnv) -> str:
    return DB_ENGINE_LUT[phenobase_env]


def get_engine_postgresql():
    """Create a PostgreSQL engine to connect to "test" or "production" database.
    Used for:
    1. Running the Phenobase API (FastAPI) in production or test mode.
    2. Running integration tests that require a real database connection.
    3. Running specific PostgreSQL-specific features, such as PostGIS spatial queries
    """

    phenobase_env = PhenobaseEnv(os.getenv("PHENOBASE_ENV"))
    dbname = get_database_name(phenobase_env)
    print(f"Using database: {dbname}")

    if phenobase_env == PhenobaseEnv.TEST_DOCKER:
        user = os.getenv("DOCKER_DB_USER")
        password = os.getenv("DOCKER_DB_PASSWORD")
        host = os.getenv("DOCKER_DB_HOST")
        port = os.getenv("DOCKER_DB_PORT")

    elif phenobase_env in [PhenobaseEnv.TEST, PhenobaseEnv.PRODUCTION]:
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
    else:
        raise ValueError(f"Unsupported environment: {phenobase_env}")

    url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
    engine = create_engine(
        url,
        pool_size=5,  # Phenobase currently only serves a small number of possible concurrent requests, so a small pool is sufficient
        max_overflow=5,  # Small cushion if there are additional requests, but not too many to avoid overwhelming the database
        pool_pre_ping=True,  # Make sure the connection is still alive before using it, to avoid errors due to stale connections
    )

    return engine


@contextmanager
def open_db_session():
    """Yield a context manager of db session for Pytest Fixtures"""
    with Session(get_engine_postgresql()) as session:
        yield session

def get_db_session():
    """Yield a generator for the FastAPI session"""
    with open_db_session() as session:
        yield session
