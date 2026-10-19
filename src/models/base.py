"""Base models to reduce boilerplate for SQLModel and Pydantic models."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, model_validator
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

    @model_validator(mode="after")
    def require_one_mutable_field(self):
        """Require at least one mutable field besides id, mode, and updater_id for update operations."""
        provided_fields = self.model_fields_set - {"id", "mode", "updater_id"}
        if all(getattr(self, field) is None for field in provided_fields):
            raise ValueError(
                "At least one mutable field must be provided for update operations besides id, mode, and updater_id."
            )
        return self


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
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        # Runtime works perfectly. mypy fails because SQLModel's internal Field()
        # type definitions don't support instantiated SQLAlchemy types (with parentheses) well.
        nullable=False,
        sa_column_kwargs={"default": utc_now},
    )
    updater_id: int = Field(foreign_key="users.id")
    updated_at: datetime | None = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        # Runtime works perfectly. mypy fails because SQLModel's internal Field()
        # type definitions don't support instantiated SQLAlchemy types (with parentheses) well.
        nullable=False,
        sa_column_kwargs={"default": utc_now, "onupdate": utc_now},
    )
