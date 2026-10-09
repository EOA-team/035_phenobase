"""SQL Model and Pydantic models for the plots table."""

from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import BIGINT, Column, UniqueConstraint
from sqlmodel import TEXT, Field, SQLModel

from src.models.base import AutoIncrementBase, DataLineageBase


class PlotBase(SQLModel):
    """Base SQL model for the plot table"""

    plot_collection_id: int = Field(foreign_key="plot_collections.id", sa_type=BIGINT)
    label: str = Field(sa_type=TEXT)
    row: int
    col: int


class Plot(AutoIncrementBase, DataLineageBase, PlotBase, table=True):
    """SQLModel model for the plot table."""

    __tablename__ = "plots"
    __table_args__ = (UniqueConstraint("plot_collection_id", "row", "col"),)
    geometry: Any = Field(
        default=None,
        sa_column=Column(
            Geometry(geometry_type="POLYGON", srid=2056),
            nullable=False,
        ),
    )
