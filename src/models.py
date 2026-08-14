from sqlmodel import Field, SQLModel

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

