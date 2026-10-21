"""SQL Model and Pydantic models for the users table."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel
from sqlmodel import TEXT, Field, SQLModel

from src.models.base import AutoIncrementBase, Delete, Insert, Update


class UserRole(StrEnum):
    """Currently supported user roles."""

    admin = "admin"
    reader = "reader"
    writer = "writer"


class UserStatus(StrEnum):
    """Currently supported user statuses."""

    active = "active"
    inactive = "inactive"


class UserRead(BaseModel):
    """Response model for reading user data via API
    Excludes sensitive information like key_hash."""

    id: int
    f_account: str | None
    firstname: str
    lastname: str
    status: UserStatus
    role: UserRole | None
    email: str
    # Note: key_hash is intentionally omitted for security reasons.


class APIKeyHashRead(BaseModel):
    """Response model for reading API key and hash data via API."""

    api_key: str
    key_hash: str


class UserBase(SQLModel):
    """Base SQL model for the users table."""

    f_account: str | None = Field(default=None, sa_type=TEXT, unique=True)
    firstname: str = Field(sa_type=TEXT)
    lastname: str = Field(sa_type=TEXT)
    status: UserStatus = Field(sa_type=TEXT)
    role: UserRole | None = Field(default=None, sa_type=TEXT)
    email: str = Field(sa_type=TEXT)
    key_hash: str | None = Field(default=None, max_length=64, unique=True)


class UserInsert(UserBase, Insert):
    """For inserting the id is not needed, as it will be auto-generated."""


class UserUpdate(Update):
    """For updating id, mode and at least one mutable field are needed."""
    f_account: str | None = Field(default=None, sa_type=TEXT, unique=True)
    firstname: str | None  = Field(sa_type=TEXT)
    lastname: str | None = Field(sa_type=TEXT)
    status: UserStatus | None = Field(sa_type=TEXT)
    role: UserRole | None = Field(default=None, sa_type=TEXT)
    email: str | None = Field(sa_type=TEXT)
    key_hash: str | None = Field(default=None, max_length=64, unique=True)


class UserDelete(Delete):
    """For deleting a user, only the id is needed."""


class User(AutoIncrementBase, UserBase, table=True):
    """SQLModel model for the users table."""

    __tablename__ = "users"
