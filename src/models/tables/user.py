from enum import StrEnum

from pydantic import BaseModel
from sqlmodel import Field

from src.models.base import AutoIncrementBase


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
    Excludes sensitive/not needed information like key_hash and id."""

    f_account: str
    firstname: str
    lastname: str
    status: UserStatus
    role: UserRole
    email: str
    # Note: key_hash is intentionally omitted for security reasons.
    # Note: id is intentionally omitted as it is not needed for reading user data.


class APIKeyHashRead(BaseModel):
    """Response model for reading API key and hash data via API."""

    api_key: str
    key_hash: str


class User(AutoIncrementBase, table=True):
    """Base SQLModel model for the users table."""

    __tablename__ = "users"
    f_account: str | None = Field(default=None, max_length=32, unique=True)
    firstname: str = Field(max_length=255)
    lastname: str = Field(max_length=255)
    status: UserStatus = Field(max_length=32)
    role: UserRole | None = Field(default=None, max_length=32)
    email: str = Field(max_length=255)
    key_hash: str | None = Field(default=None, max_length=64, unique=True)
