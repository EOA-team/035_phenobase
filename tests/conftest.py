import json
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel

from src.db import PhenobaseEnv, get_database_name, get_engine
from src.models.tables.user import User

SEEDS_FOLDER = Path(__file__).resolve().parent.parent / "seeds"


@pytest.fixture(scope="session")
def phenobase_db_minimal_postgres():
    """Fixture to set initialize the  PostgresSQL test database which 
    is running on a real server.
    Note: This Fixture is used for integration tests."""
    engine = get_engine()
    active_db_name = engine.url.database
    if active_db_name != get_database_name(PhenobaseEnv.TEST):
        raise ValueError(
            f"Refusing to run test on a non-test databae: {engine.url.database}"
        )

    # Drop all tables to ensure a clean slate
    SQLModel.metadata.drop_all(engine)
    # Create all tables defined in the SQLModel metadata
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        users = json.loads(
            (SEEDS_FOLDER / "test_users.json").read_text(encoding="utf-8")
        )
        session.add_all([User(**user) for user in users])
        session.commit()
        yield session  # Provide the session to the test functions
        SQLModel.metadata.drop_all(engine)  # Clean up after tests

@pytest.fixture(scope="session")
def phenobase_db_mock_sqlite():
    """Fixture to set initialize the in-memory SQLite test database which 
    runs also on a CI/CD pipeline.
    Note: This Fixture is used for unit tests."""
    engine = get_engine(use_sqlite=True)
  
    # Drop all tables to ensure a clean slate
    SQLModel.metadata.drop_all(engine)
    # Create all tables defined in the SQLModel metadata
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        users = json.loads(
            (SEEDS_FOLDER / "test_users.json").read_text(encoding="utf-8")
        )
        session.add_all([User(**user) for user in users])
        session.commit()
        yield session  # Provide the session to the test functions
        SQLModel.metadata.drop_all(engine)  # Clean up after tests
