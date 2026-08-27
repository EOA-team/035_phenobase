"""Database engine and session management for Phenobase."""

import os
from enum import StrEnum

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlmodel import Session
from sqlalchemy.pool import StaticPool

load_dotenv()


class PhenobaseEnv(StrEnum):
    TEST = "test"
    PRODUCTION = "production"


DB_NAME_LUT = {
    PhenobaseEnv.TEST: "test_phenobase",
    PhenobaseEnv.PRODUCTION: "phenobase",
}


def get_database_name(phenobase_env: PhenobaseEnv) -> str:
    return DB_NAME_LUT[phenobase_env]


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

def get_engine_sqlite():
    """Create an in-memory SQLite engine .
    Used For:
    1. Running unit tests on CI/CD pipelines (Docker) that do not have access to a PostgreSQL database.
    2. Running unit tests that do not require PostgreSQL-specific features, such as PostGIS spatial queries.

    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


def  get_engine(use_sqlite: bool = False):
    """Create the SQLAlchemy engine .
    
    Default: Return the PostgreSQL engine for the current environment (test or production).
    use_sqlite=True: Return an in-memory SQLite engine that can run tests on a CI/CD pipeline (Docker) without access to real PostgreSQL Server.
    """
    if use_sqlite:
        return get_engine_sqlite()
    else:
        return get_engine_postgresql()


def get_db_session():
    """Yield a database session for FastAPI dependency injection."""
    with Session(get_engine()) as session:
        yield session
