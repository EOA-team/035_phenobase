import json
from pathlib import Path

import pytest
from sqlmodel import SQLModel

from src.db import open_db_session
from src.models.tables.user import User
from src.settings import DeployStage, Settings

SEEDS_FOLDER = Path(__file__).resolve().parent.parent / "seeds"


@pytest.fixture(autouse=True)
def production_safeguard():
    """Refuse to run any tests on production"""
    settings = Settings()
    if settings.deploy_stage is DeployStage.PRODUCTION:
        pytest.skip(
            "DEPLOY_STAGE=production — Safeguard prevents running tests on production."
        )


@pytest.fixture(scope="session")
def phenobase_db_minimal():
    """Fixture to set up a minimal test database for integration tests."""
    with open_db_session() as session:
        engine = session.get_bind()
        active_db_name = engine.url.database
        print(active_db_name)

        # Drop all tables to ensure a clean slate
        SQLModel.metadata.drop_all(engine)
        # Create all tables defined in the SQLModel metadata
        SQLModel.metadata.create_all(engine)

        users = json.loads(
            (SEEDS_FOLDER / "test_users.json").read_text(encoding="utf-8")
        )
        session.add_all([User(**user) for user in users])
        session.commit()
        yield session  # Provide the session to the test functions
        SQLModel.metadata.drop_all(engine)  # Clean up after tests
