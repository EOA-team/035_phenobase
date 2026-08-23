import pandas as pd
from sqlmodel import Session, select

from src.data_upload import UPLOAD_SCHEMA_REGISTRY, UploadTables


def get_db_table_as_df(session: Session, table_name: UploadTables) -> pd.DataFrame:
    """Export a database table to a CSV file."""
    sql_table = UPLOAD_SCHEMA_REGISTRY.get(UploadTables(table_name)).table_model
    rows = session.exec(select(sql_table)).all()
    df = pd.DataFrame([row.model_dump() for row in rows])
    return df
