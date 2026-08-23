import pandas as pd
from sqlmodel import Session, SQLModel, select

from src.models import SCHEMA_REGISTRY, UploadTables


def get_db_table_as_pd(session: Session, table_name: UploadTables) -> pd.DataFrame:
    """Return all rows of a database table as a pandas DataFrame."""
    schema = SCHEMA_REGISTRY.get(UploadTables(table_name))
    if schema is None:
        raise ValueError(f"Unsupported table: {table_name}")
    query = select(schema.table_model)
    rows = list(session.exec(query).all())
    return pd.DataFrame([row.model_dump() for row in rows])
