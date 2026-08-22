from datetime import datetime
from enum import StrEnum
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
class User(SQLModel, table=True):
    """SQLModel model for the users table."""

    __tablename__ = "users"
    id: int | None = Field(
        default=None, primary_key=True
    )  # Auto-incrementing primary key
    f_account: str | None = Field(default=None, max_length=32, unique=True)
    firstname: str = Field(max_length=255)
    lastname: str = Field(max_length=255)
    status: Status = Field(max_length=32)
    role: Role | None = Field(default=None, max_length=32)
    email: str = Field(max_length=255)
    key_hash: str | None = Field(default=None, max_length=64, unique=True)


class CropTypeBase(BaseModel):
    name: str = Field(max_length=255)
    code: str = Field(max_length=32, unique=True)
    description: str = Field(sa_type=TEXT)
    doc_path: str = Field(sa_type=TEXT)


class CropType(SQLModel, CropTypeBasetable=True):
    """SQLModel model for the crop_type table."""

    __tablename__ = "crop_types"
    id: int | None = Field(
        default=None, primary_key=True
    )  # Auto-incrementing primary key
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


class CropTypeInsert(CropTypeBase):
    """For inserting the id is not needed, as it will be auto-generated."""

    mode: Literal[UploadModes.INSERT] = UploadModes.INSERT
    creator_id: int


class CropTypeUpdate(CropTypeBase):
    """For updating only the updater_id is needed."""

    mode: Literal[UploadModes.UPDATE] = UploadModes.UPDATE
    id: int
    updater_id: int


class CropTypeDelete(BaseModel):
    """For deleting a CropType, only the id is needed."""

    mode: Literal[UploadModes.DELETE] = UploadModes.DELETE
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
