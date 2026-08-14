from sqlmodel import Field, SQLModel
from pydantic import BaseModel

from src.api import Role


class User(SQLModel, table=True):
    """SQLModel model for the users table."""

    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    f_account: str = Field(max_length=32, unique=True)
    firstname: str = Field(max_length=255)
    lastname: str = Field(max_length=255)
    role: Role = Field(max_length=32)
    email: str = Field(max_length=255)
    key_hash: str = Field(max_length=64, unique=True)


class UserRead(BaseModel):
    """Response model for reading user data via API
    Excludes sensitive/not needed information like key_hash and id."""

    f_account: str
    firstname: str
    lastname: str
    role: Role
    email: str
    # Note: key_hash is intentionally omitted for security reasons.
    # Note: id is intentionally omitted as it is not needed for reading user data.
