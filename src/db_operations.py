from typing import cast

import pandas as pd
from sqlmodel import Session, SQLModel, select

from src.models.base import UploadModes
from src.models.registry import SCHEMA_REGISTRY, UploadTables
from src.models.row_models import UploadRow, UploadRowWithId


class IdNotFoundError(Exception):
    def __init__(self, table: str, id: int):
        super().__init__(f"{table} with id={id!r} not found")
        self.table, self.id = table, id


def write_to_database(
    session: Session,
    table_name: UploadTables,
    rows: list[UploadRow],
) -> None:
    """Write validated rows to the database as insert/update/delete.

    Works for any table registered in SCHEMA_REGISTRY: the target table class
    comes from the registry, and each row model carries its own fields, so
    model_dump() always produces valid column values.

    All rows are applied within one transaction; a single commit at the end
    makes the whole file atomic: either every row lands or none does.
    """
    table = SCHEMA_REGISTRY[table_name].table_model

    try:
        for row in rows:
            match row.mode:
                case UploadModes.INSERT:
                    _insert_row(session, table, row)
                case UploadModes.UPDATE:
                    _update_row(session, table, row)
                case UploadModes.DELETE:
                    _delete_row(session, table, row)
                case _:
                    raise ValueError(f"Unsupported upload mode: {row.mode!r}")

        session.commit()

    except Exception:
        session.rollback()
        raise


def _insert_row(session: Session, table: type[SQLModel], row: UploadRow) -> None:
    """Insert a new row; the id is auto-generated."""
    session.add(table(**row.model_dump(exclude={"mode"})))


def _update_row(session: Session, table: type[SQLModel], row: UploadRow) -> None:
    """Update an existing row by id (if id is valid); only fields that are not None."""
    row_id = cast(UploadRowWithId, row).id
    obj = session.get(table, row_id)
    if obj is None:
        raise IdNotFoundError(str(table.__tablename__), row_id)
    for field, value in row.model_dump(
        exclude={"mode", "id"}, exclude_none=True
    ).items():
        setattr(obj, field, value)


def _delete_row(session: Session, table: type[SQLModel], row: UploadRow) -> None:
    """Delete an existing row by id (if id is valid)."""
    row_id = cast(UploadRowWithId, row).id
    obj = session.get(table, row_id)
    if obj is None:
        raise IdNotFoundError(str(table.__tablename__), row_id)
    session.delete(obj)


def table_is_empty(session: Session, table_name: UploadTables) -> bool:
    """Return True if the given table has no rows."""
    schema = SCHEMA_REGISTRY.get(UploadTables(table_name))
    if schema is None:
        raise ValueError(f"Unsupported table: {table_name}")
    return session.exec(select(schema.table_model).limit(1)).first() is None


def get_db_table(session: Session, table_name: UploadTables) -> pd.DataFrame:
    """Return all rows of a database table as a pandas DataFrame."""
    schema = SCHEMA_REGISTRY.get(UploadTables(table_name))
    if schema is None:
        raise ValueError(f"Unsupported table: {table_name}")
    query = select(schema.table_model)
    rows = list(session.exec(query).all())
    df = pd.DataFrame([row.model_dump() for row in rows])
    return df
