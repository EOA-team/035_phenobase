from sqlmodel import Session, SQLModel, select

from src.models import SCHEMA_REGISTRY, UploadTables


def get_db_table_as_rows(
    session: Session, table_name: UploadTables
) -> list[SQLModel]:
    """Return all rows of a database table as model instances."""
    schema = SCHEMA_REGISTRY.get(UploadTables(table_name))
    if schema is None:
        raise ValueError(f"Unsupported table: {table_name}")
    return list(session.exec(select(schema.table_model)).all())
