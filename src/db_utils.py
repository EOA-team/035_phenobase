from typing import Any

import pandas as pd
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from sqlmodel import Session, select

from src.models.registry import SCHEMA_REGISTRY, ManagedTables


def _geometry_to_wkt(value: Any) -> Any:
    """Return the WKT text of a geometry value, or the value itself."""
    return to_shape(value).wkt if isinstance(value, WKBElement) else value


def get_db_table_as_pd(session: Session, table_name: ManagedTables) -> pd.DataFrame:
    """Return all rows of a database table as a pandas DataFrame."""
    schema = SCHEMA_REGISTRY.get(ManagedTables(str(table_name)))
    if schema is None:
        raise ValueError(f"Unsupported table: {table_name}")
    query = select(schema.table_model)
    rows = list(session.exec(query).all())
    df = pd.DataFrame([row.model_dump() for row in rows])
    df = df.map(_geometry_to_wkt)
    if schema.read_order is not None:
        df = df[schema.read_order]
    return df


def table_is_empty(session: Session, table_name: ManagedTables) -> bool:
    """Return True if the given table has no rows."""
    schema = SCHEMA_REGISTRY.get(ManagedTables(str(table_name)))
    if schema is None:
        raise ValueError(f"Unsupported table: {table_name}")
    return session.exec(select(schema.table_model).limit(1)).first() is None
