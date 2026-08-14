"""Loads the base users into the database.
One user with reader role and one user with writer role are created.
API Keys are generated using the create_api_key.py script and their key hashes are stored in the database."""

import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlmodel import SQLModel

from src.db import get_engine
from src.models import Role, User

load_dotenv()
BASE_USERS = [
    User(
        f_account=os.getenv("NORMAL_USER"),
        firstname=os.getenv("NORMAL_USER_FIRSTNAME"),
        lastname=os.getenv("NORMAL_USER_LASTNAME"),
        role=Role.reader,
        email=os.getenv("NORMAL_USER_EMAIL"),
        key_hash=os.getenv("NORMAL_USER_KEY_HASH"),
    ),
    User(
        f_account=os.getenv("SERVICE_USER"),
        firstname=os.getenv("SERVICE_USER_FIRSTNAME"),
        lastname=os.getenv("SERVICE_USER_LASTNAME"),
        role=Role.writer,
        email=os.getenv("SERVICE_USER_EMAIL"),
        key_hash=os.getenv("SERVICE_USER_KEY_HASH"),
    ),
]

if __name__ == "__main__":
    phenobase_engine = get_engine()

    SQLModel.metadata.create_all(phenobase_engine)
    #SQLModel.metadata.drop_all(phenobase_engine)

    with Session(phenobase_engine) as session:
        session.add_all(BASE_USERS)
        session.commit()
