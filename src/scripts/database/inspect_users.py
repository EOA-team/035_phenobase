"""Inspect Users table in the database and print its contents."""

import pandas as pd
from sqlalchemy import inspect
from sqlmodel import select

from src.db import get_engine
from src.models.tables.user import User

if __name__ == "__main__":
    phenobase_engine = get_engine()
    inspector = inspect(phenobase_engine)
    print(inspector.get_table_names())

    if "users" not in inspector.get_table_names():
        print("Users table does not exist. Please run load_users.py first.")
    else:
        statement = select(User)
        df = pd.read_sql(statement, phenobase_engine)
        print(df)
