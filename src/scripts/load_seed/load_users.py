"""Loads the base users into the database.
One user with reader role and one user with writer role are created.
API Keys are generated using the create_api_key.py script and their key hashes are stored in the database."""

import os
import json

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlmodel import SQLModel
from pathlib import Path

import smbclient
from src.db import get_engine
from src.nas_helper import build_unc_path, connect_to_nas, Password as NasPw, User as NasUser
from src.models import User

load_dotenv()
# Real users data, that can be used for testing 
SEED_FOLDER = r"drone\phenobase\seed\test_db"


def load_users_from_nas()->list[dict]:
    """Load users data from the NAS."""
    seed_path = build_unc_path(
        hostname=os.getenv("NAS_RECKENHOLZ"),
        share="Data-EODrone",
        folder=SEED_FOLDER
    )
    users_filepath = Path(seed_path) / "users.json"
    connect_to_nas(user_type=NasUser.NORMAL, password=NasPw.NORMAL)
    with smbclient.open_file(users_filepath, "r", encoding="utf-8") as f:
        users_data = json.load(f)
        return users_data
    
if __name__ == "__main__":
    users_data = load_users_from_nas()
    phenobase_engine = get_engine()

    User.__table__.drop(phenobase_engine, checkfirst=True)  # Drop the users table if it exists
    SQLModel.metadata.create_all(phenobase_engine) #Recreare all tables

    with Session(phenobase_engine) as session:
        session.add_all([User(**user) for user in users_data])
        session.commit()
