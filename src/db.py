"""Database engine and session management for Phenobase."""
import os
from enum import StrEnum

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


class PHENOBASE_ENV(StrEnum):
    TEST = "test"
    PRODUCTION = "production"


DB_NAME_LUT = {
    PHENOBASE_ENV.TEST: "test_phenobase",
    PHENOBASE_ENV.PRODUCTION: "phenobase",
}


def get_database_name(phenobase_env: PHENOBASE_ENV) -> str:
    return DB_NAME_LUT[phenobase_env]


def get_engine():
    """Create a SQLAlchemy engine for the specified database."""

    phenobase_env = PHENOBASE_ENV(os.getenv("PHENOBASE_ENV"))
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
        pool_pre_ping=True,  # Make sure theyes but in the test i would want to c connection is alive before using it
    )

    return engine
