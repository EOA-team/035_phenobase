"""SQL Model and Pydantic models for the units table."""

from sqlmodel import TEXT, Field, SQLModel

from src.models.base import AutoIncrementBase, DataLineageBase, Delete, Insert, Update


class UnitBase(SQLModel):
    """Base SQL model for the unit table"""

    name: str = Field(max_length=255)
    code: str = Field(max_length=32, unique=True)
    description: str = Field(sa_type=TEXT)


class UnitInsert(UnitBase, Insert):
    """For inserting the id is not needed, as it will be auto-generated."""


class UnitUpdate(UnitBase, Update):
    """For updating the id and all other fields are needed."""


class UnitDelete(Delete):
    """For deleting a Unit, only the id is needed."""


class Unit(AutoIncrementBase, DataLineageBase, UnitBase, table=True):
    """SQLModel model for the unit table."""

    __tablename__ = "units"
