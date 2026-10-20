"""SQL Model and Pydantic models for the plots table."""

from typing import Any

from geoalchemy2 import Geometry
from pydantic import model_validator
from sqlalchemy import BIGINT, UniqueConstraint
from sqlmodel import TEXT, Field, SQLModel

from src.models.base import (
    AutoIncrementBase,
    DataLineageBase,
    Delete,
    Insert,
)


class PlotBase(SQLModel):
    """Base SQL model for the plot table — shared shapes for records and """

    plot_collection_id: int | None = Field(
        default=None,
        foreign_key="plot_collections.id",
        sa_type=BIGINT,
        nullable=False,
    )
    label: str = Field(sa_type=TEXT)
    row: int
    col: int
    geometry: Any = Field(
        default=None,
        sa_type=Geometry(geometry_type="POLYGON", srid=2056),  # type: ignore[call-overload]
        nullable=False,
    )

    @model_validator(mode="after")
    def label_matches_grid_position(self) -> "PlotBase":
        expected = f"x{self.col}_y{self.row}"
        if self.label != expected:
            raise ValueError(
                f"Label '{self.label}' does not match grid position "
                f"col={self.col}, row={self.row} (expected '{expected}')."
            )
        return self


class Plot(AutoIncrementBase, DataLineageBase, PlotBase, table=True):
    """SQLModel model for the plot table."""

    __tablename__ = "plots"
    __table_args__ = (UniqueConstraint("plot_collection_id", "row", "col"),)


class PlotInsert(PlotBase, Insert):
    """For inserting the id is not needed, as it will be auto-generated."""


class PlotDelete(Delete):
    """For deleting a Plot, only the id is needed."""

# Note: Update for single plots not supported, only update for whole plot_collection!
