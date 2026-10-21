"""Database engine and session management for Phenobase."""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlmodel import Session

from src.settings import DatabaseName, DeployStage, Settings


def get_database_name(deploy_stage: DeployStage) -> DatabaseName:
    """Return the database name based on the deploy stage."""
    if deploy_stage == DeployStage.PRODUCTION:
        return DatabaseName.PHENOBASE
    elif deploy_stage == DeployStage.TEST:
        return DatabaseName.TEST_PHENOBASE


def get_engine_postgresql():
    """Return a SQLAlchemy engine for the PostgreSQL database based on the settings."""
    settings = Settings()
    dbs = Settings().database

    url = URL.create(
        drivername="postgresql+psycopg",
        username=dbs.user,
        password=dbs.password.get_secret_value(),
        host=dbs.host,
        port=dbs.port,
        database=get_database_name(settings.deploy_stage),
    )

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
