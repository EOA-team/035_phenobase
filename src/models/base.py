"""Base models to reduce boilerplate for SQLModel and Pydantic models."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Get the current UTC time."""
    return datetime.now(tz=UTC)


class UploadModes(StrEnum):
    """Phenobase API supported modes for Upload"""

    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


class UploadFileType(StrEnum):
    """Phenobase API supported file types."""

    CSV = "csv"
    GEOJSON = "geojson"


class Insert(BaseModel):
    """Required file fields for insert operations."""

    mode: Literal[UploadModes.INSERT]
    creator_id: int
    updater_id: int


class Update(BaseModel):
    """Required file fields for update operations."""

    id: int
    mode: Literal[UploadModes.UPDATE]
    updater_id: int


class Delete(BaseModel):
    """Required file fields for delete operations."""

    id: int
    mode: Literal[UploadModes.DELETE]


class AutoIncrementBase(SQLModel):
    """Base SQL model for auto-incrementing primary key."""

    id: int | None = Field(default=None, primary_key=True)


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
