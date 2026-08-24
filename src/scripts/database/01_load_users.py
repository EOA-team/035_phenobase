"""Loads initial users into the database.

Users are only inserted if the users table is empty, making the script idempotent."""

import json
import os
from pathlib import Path

import smbclient
from dotenv import load_dotenv
from sqlmodel import Session, select

from src.db import PhenobaseEnv, get_engine
from src.models.models import User
from src.nas_helper import Password as NasPw
from src.nas_helper import User as NasUser
from src.nas_helper import build_unc_path, connect_to_nas
from src.scripts.script_utils import confirm_production

load_dotenv()
# Real users data, that can be used for testing
SEED_FOLDER = r"drone\phenobase\production\seed"


def load_users_from_nas() -> list[dict]:
    """Load users data from the NAS."""
    seed_path = build_unc_path(
        hostname=os.getenv("NAS_RECKENHOLZ"), share="Data-EODrone", folder=SEED_FOLDER
    )
    users_filepath = Path(seed_path) / "users.json"
    connect_to_nas(user_type=NasUser.NORMAL, password=NasPw.NORMAL)
    with smbclient.open_file(users_filepath, "r", encoding="utf-8") as f:
        users_data = json.load(f)
        return users_data


if __name__ == "__main__":
    phenobase_environment = PhenobaseEnv(os.getenv("PHENOBASE_ENV"))
    if phenobase_environment == PhenobaseEnv.PRODUCTION:
        confirm_production()

    users_data = load_users_from_nas()
    engine = get_engine()

    with Session(engine) as session:
        table_has_users = session.exec(select(User.id)).first() is not None
        if table_has_users:
            print("Users table is not empty, skipping insert.")
            raise SystemExit("Aborted.")
        session.add_all([User(**user) for user in users_data])
        session.commit()
        print(f"Inserted {len(users_data)} users.")
