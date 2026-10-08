"""SQL Model and Pydantic models for the crop_types table."""

from sqlmodel import TEXT, Field, SQLModel

from src.models.base import AutoIncrementBase, DataLineageBase, Delete, Insert, Update


class CropTypeBase(SQLModel):
    """Base SQL model for the crop_type table"""

    name: str = Field(sa_type=TEXT, unique=True)
    code: str = Field(sa_type=TEXT, unique=True)
    description: str = Field(sa_type=TEXT)
    doc_path: str | None = Field(default=None, sa_type=TEXT)


class CropTypeInsert(CropTypeBase, Insert):
    """For inserting the id is not needed, as it will be auto-generated."""


class CropTypeUpdate(CropTypeBase, Update):
    """For updating the id and all other fields are needed."""


class CropTypeDelete(Delete):
    """For deleting a CropType, only the id is needed."""


class CropType(AutoIncrementBase, DataLineageBase, CropTypeBase, table=True):
    """SQLModel model for the crop_type table."""

    __tablename__ = "crop_types"
