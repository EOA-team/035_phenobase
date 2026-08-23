from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import UnionType
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import DateTime
from sqlmodel import TEXT, Field, SQLModel

from src.api import Role, Status
from src.time_utils import utc_now

# Base models for insert, update, and delete
############################################


class UploadModes(StrEnum):
    """Phenobase API supported modes for Upload"""

    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


class Insert(BaseModel):
    """SQLModel model for Inserts"""

    id: int
    mode: UploadModes.INSERT
    creator_id: int


class Update(BaseModel):
    """SQLModel model for Updates"""

    id: int
    mode: UploadModes.UPDATE
    updater_id: int


class Delete(BaseModel):
    """SQLModel model for Deletes"""

    id: int
    mode: UploadModes.DELETE


############################################


class AutoIncrementBase(SQLModel):
    """Base SQL model for auto-incrementing primary key."""

    id: int | None = Field(default=None, primary_key=True)


class User(AutoIncrementBase, table=True):
    """Base SQLModel model for the users table."""

    __tablename__ = "users"
    f_account: str | None = Field(default=None, max_length=32, unique=True)
    firstname: str = Field(max_length=255)
    lastname: str = Field(max_length=255)
    status: Status = Field(max_length=32)
    role: Role | None = Field(default=None, max_length=32)
    email: str = Field(max_length=255)
    key_hash: str | None = Field(default=None, max_length=64, unique=True)


class DataLineageBase(SQLModel):
    """Base SQL model for data lineage information."""

    creator_id: int = Field(foreign_key="users.id")
    created_at: datetime | None = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": False},
    )
    updater_id: int = Field(foreign_key="users.id")
    updated_at: datetime | None = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "nullable": False,
            "onupdate": utc_now,
        },
    )


class CropTypeBase(SQLModel):
    """Base SQL model for the crop_type table"""

    name: str = Field(max_length=255)
    code: str = Field(max_length=32, unique=True)
    description: str = Field(sa_type=TEXT)
    doc_path: str = Field(sa_type=TEXT)


class CropType(AutoIncrementBase, DataLineageBase, CropTypeBase, table=True):
    """SQLModel model for the crop_type table."""

    __tablename__ = "crop_types"


class CropTypeInsert(CropTypeBase):
    """For inserting the id is not needed, as it will be auto-generated."""

    mode: Literal[UploadModes.INSERT]
    creator_id: int
    updater_id: int


class CropTypeUpdate(CropTypeBase):
    """For updating only the updater_id is needed."""

    mode: Literal[UploadModes.UPDATE]
    id: int
    updater_id: int


class CropTypeDelete(BaseModel):
    """For deleting a CropType, only the id is needed."""

    mode: Literal[UploadModes.DELETE]
    id: int


class UserRead(BaseModel):
    """Response model for reading user data via API
    Excludes sensitive/not needed information like key_hash and id."""

    f_account: str
    firstname: str
    lastname: str
    status: Status
    role: Role
    email: str
    # Note: key_hash is intentionally omitted for security reasons.
    # Note: id is intentionally omitted as it is not needed for reading user data.


class APIKeyHashRead(BaseModel):
    """Response model for reading API key and hash data via API."""

    api_key: str
    key_hash: str


class FileType(StrEnum):
    """Phenobase API supported file types."""

    CSV = "csv"
    GEOJSON = "geojson"


@dataclass(frozen=True)
class TableSchema:
    """Configuration for one API-managed table.

    row_model:    Pydantic Basemodel (or union of insert/update/delete models) used to
                  validate each uploaded record.
    table_model:  SQLModel class (declared with table=True) the validated records
                  are written to.
    read_model:   SQLModel class used as the API response model for reading this
                  table.
    read_order:   Optional explicit column order for reading this table. If None,
                  the model's natural field order is used.
    filetype:     File format the API accepts for this table.
    """

    row_model: type[BaseModel] | UnionType
    table_model: type[SQLModel]
    read_model: type[SQLModel]
    filetype: FileType
    read_order: list[str] | None = None

    def __post_init__(self) -> None:
        # SQLAlchemy attaches __table__ only to classes declared with table=True,
        # so this guards against accidentally registering a non-table model.
        if getattr(self.table_model, "__table__", None) is None:
            raise TypeError(
                f"{self.table_model.__name__} is not a SQLModel table "
                f"(missing table=True / __table__)."
            )


class UploadTables(StrEnum):
    """Tables managed by the Phenobase API."""

    CROP_TYPE = "crop_type"
    CROP_PLOT = "crop_plot"


# Configuration for each API-managed table: row model(s), target table, read model,
# and accepted filetype.
SCHEMA_REGISTRY: dict[UploadTables, TableSchema] = {
    UploadTables.CROP_TYPE: TableSchema(
        row_model=CropTypeInsert | CropTypeUpdate | CropTypeDelete,
        table_model=CropType,
        read_model=CropType,
        filetype=FileType.CSV,
        read_order=[
            "id",
            "name",
            "code",
            "description",
            "creator_id",
            "created_at",
            "updater_id",
            "updated_at",
            "doc_path",
        ],
    ),
}
