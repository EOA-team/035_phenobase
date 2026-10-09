"""Resets the whole database by dropping and recreating all tables.
Warning: All data in the database will be lost."""

from dotenv import load_dotenv
from sqlmodel import SQLModel

from src.db import get_engine_postgresql

# Tables used by SQLModel metadata
from src.models.tables import (  # noqa: F401
    crop_type,
    plot,
    plot_collection,
    treatment,
    unit,
    user,
    variable,
)
from src.scripts.script_utils import confirm_production
from src.settings import DeployStage, Settings

load_dotenv()


def reset_database() -> None:
    """Drop and recreate all tables defined in the SQLModel metadata."""
    engine = get_engine_postgresql()
    SQLModel.metadata.drop_all(
        engine,
    )
    SQLModel.metadata.create_all(engine)
    print("Database reset: all tables dropped and recreated.")


if __name__ == "__main__":
    settings = Settings()
    if settings.deploy_stage == DeployStage.PRODUCTION:
        confirm_production()
    reset_database()
