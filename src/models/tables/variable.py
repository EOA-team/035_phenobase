"""SQL Model and Pydantic models for the variables table."""

from sqlmodel import TEXT, Field, SQLModel

from src.models.base import AutoIncrementBase, DataLineageBase, Delete, Insert, Update


class VariableBase(SQLModel):
    """Base SQL model for the variable table"""

    name: str = Field(sa_type=TEXT, unique=True)
    code: str = Field(sa_type=TEXT, unique=True)
    description: str = Field(sa_type=TEXT)
    doc_path: str | None = Field(default=None, sa_type=TEXT)


class VariableInsert(VariableBase, Insert):
    """For inserting the id is not needed, as it will be auto-generated."""


class VariableUpdate(VariableBase, Update):
    """For updating the id and all other fields are needed."""


class VariableDelete(Delete):
    """For deleting a Variable, only the id is needed."""


class Variable(AutoIncrementBase, DataLineageBase, VariableBase, table=True):
    """SQLModel model for the variables table."""

    __tablename__ = "variables"
