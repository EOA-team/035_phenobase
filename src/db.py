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
    TEST = "test"
    PRODUCTION = "production"
    CI_TEST = "ci_test"


class EngineType(StrEnum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


DB_NAME_LUT = {
    PhenobaseEnv.TEST: "test_phenobase",
    PhenobaseEnv.PRODUCTION: "phenobase",
}

DB_ENGINE_LUT = {
    PhenobaseEnv.TEST: EngineType.POSTGRESQL,
    PhenobaseEnv.PRODUCTION: EngineType.POSTGRESQL,
    PhenobaseEnv.CI_TEST: EngineType.SQLITE,
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

    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")

    url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
    engine = create_engine(
        url,
        pool_size=5,  # Phenobase currently only serves a small number of possible concurrent requests, so a small pool is sufficient
        max_overflow=5,  # Small cushion if there are additional requests, but not too many to avoid overwhelming the database
        pool_pre_ping=True,  # Make sure the connection is still alive before using it, to avoid errors due to stale connections
    )

    return engine


@cache
def get_engine_sqlite():
    """Create an in-memory SQLite engine .
    Used For:
    1. Running unit tests on CI/CD pipelines (Docker)

    @cache returns the SAME engine on every call: an in-memory SQLite
    database lives inside its engine/connection (StaticPool), so creating
    a new engine per call would give each caller its own empty database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@contextmanager
def open_db_session():
    """Yield a context manager of db session for Pytest Fixtures"""
    phenobase_env = PhenobaseEnv(os.getenv("PHENOBASE_ENV"))
    engine_type = get_engine_type(phenobase_env)
    if engine_type == EngineType.POSTGRESQL:
        with Session(get_engine_postgresql()) as session:
            yield session
    elif engine_type == EngineType.SQLITE:
        with Session(get_engine_sqlite()) as session:
            yield session
    else:
        raise ValueError(f"Unsupported engine type: {engine_type}")


def get_db_session():
    """Yield a generator for the FastAPI session"""
    with open_db_session() as session:
        yield session
