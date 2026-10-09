"""SQL Model and Pydantic models for the plot_collections table."""

from sqlmodel import TEXT, Field, SQLModel

from src.models.base import AutoIncrementBase, DataLineageBase, Delete, Insert, Update


class PlotCollectionBase(SQLModel):
    """Base SQL model for the plot_collection table"""

    name: str = Field(sa_type=TEXT, unique=True)
    category: str = Field(sa_type=TEXT)
    crs: str = Field(sa_type=TEXT)


class PlotCollectionInsert(PlotCollectionBase, Insert):
    """For inserting the id is not needed, as it will be auto-generated."""


class PlotCollectionUpdate(PlotCollectionBase, Update):
    """For updating the id and all other fields are needed."""


class PlotCollectionDelete(Delete):
    """For deleting a plot_collection, only the id is needed."""


class PlotCollection(AutoIncrementBase, DataLineageBase, PlotCollectionBase, table=True):
    """SQLModel model for the plot_collection table."""

    __tablename__ = "plot_collections"
