"""Database engine and session management for Phenobase."""

import os
from enum import StrEnum

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlmodel import Session

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


def get_engine():
    """Create a SQLAlchemy engine for the specified database."""

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


def get_db_session():
    """Yield a database session for FastAPI dependency injection."""
    with Session(get_engine()) as session:
        yield session
