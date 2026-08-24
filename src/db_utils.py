import pandas as pd
from sqlmodel import Session, select

from src.models.registry import SCHEMA_REGISTRY, UploadTables


def get_db_table_as_pd(session: Session, table_name: UploadTables) -> pd.DataFrame:
    """Return all rows of a database table as a pandas DataFrame."""
    schema = SCHEMA_REGISTRY.get(UploadTables(table_name))
    if schema is None:
        raise ValueError(f"Unsupported table: {table_name}")
    query = select(schema.table_model)
    rows = list(session.exec(query).all())
    df = pd.DataFrame([row.model_dump() for row in rows])
    if schema.read_order is not None:
        df = df[schema.read_order]
    return df


def table_is_empty(session: Session, table_name: UploadTables) -> bool:
    """Return True if the given table has no rows."""
    schema = SCHEMA_REGISTRY.get(UploadTables(table_name))
    if schema is None:
        raise ValueError(f"Unsupported table: {table_name}")
    return session.exec(select(schema.table_model).limit(1)).first() is None
