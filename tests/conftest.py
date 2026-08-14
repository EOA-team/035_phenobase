import pytest
import json
from pathlib import Path
from src.db import get_engine, PHENOBASE_ENV, get_database_name, 
from src.models import User
from sqlmodel import SQLModel, Session

SEEDS_FOLDER = Path(__file__).resolve().parent.parent / "seeds"

@pytest.fixture(scope="session")
def phenobase_db_minimal():
    """Fixture to set up a minimal test database for integration tests."""
    engine = get_engine()
    active_db_name = engine.url.database
    if active_db_name != get_database_name(PHENOBASE_ENV.TEST) :
        raise ValueError(f"Refusing to run test on a non-test databae: {engine.url.database}")
    
    # Drop all tables to ensure a clean slate
    SQLModel.metadata.drop_all(engine)
    # Create all tables defined in the SQLModel metadata
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        users = json.loads((SEEDS_FOLDER / "test_users.json").read_text(encoding="utf-8"))
        session.add_all([User(**user) for user in users])
        session.commit()
        yield session  # Provide the session to the test functions
        SQLModel.metadata.drop_all(engine)  # Clean up after tests