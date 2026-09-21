"""SQL Model and Pydantic models for the treatments table."""

from sqlmodel import TEXT, Field, SQLModel

from src.models.base import AutoIncrementBase, DataLineageBase, Delete, Insert, Update


class TreatmentBase(SQLModel):
    """Base SQL model for the treatment table"""

    name: str = Field(max_length=255)
    code: str = Field(max_length=32, unique=True)
    description: str = Field(sa_type=TEXT)
    doc_path: str = Field(sa_type=TEXT)


class TreatmentInsert(TreatmentBase, Insert):
    """For inserting the id is not needed, as it will be auto-generated."""


class TreatmentUpdate(TreatmentBase, Update):
    """For updating the id and all other fields are needed."""


class TreatmentDelete(Delete):
    """For deleting a Treatment, only the id is needed."""


class Treatment(AutoIncrementBase, DataLineageBase, TreatmentBase, table=True):
    """SQLModel model for the treatment table."""

    __tablename__ = "treatments"
