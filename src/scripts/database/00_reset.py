"""Resets the whole database by dropping and recreating all tables.
Warning: All data in the database will be lost."""

import os

from dotenv import load_dotenv
from sqlmodel import SQLModel

from src.db import PhenobaseEnv, get_engine
from src.models import models  # noqa: F401
from src.scripts.script_utils import confirm_production

load_dotenv()


def reset_database() -> None:
    """Drop and recreate all tables defined in the SQLModel metadata."""
    engine = get_engine()
    SQLModel.metadata.drop_all(
        engine,
    )
    SQLModel.metadata.create_all(engine)
    print("Database reset: all tables dropped and recreated.")


if __name__ == "__main__":
    phenobase_environment = PhenobaseEnv(os.getenv("PHENOBASE_ENV"))
    if phenobase_environment == PhenobaseEnv.PRODUCTION:
        confirm_production()
    reset_database()
