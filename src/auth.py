"""Authentication for the Phenobase API"""

import hashlib
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select

from src.api import Role
from src.db import get_db_session
from src.models import User


def get_api_key(api_key: str | None = Header(default=None, alias="X-API-Key")) -> str:
    """Extract the API key from the request headers.
    Raises an HTTPException if the API key is missing."""
    if api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")
    return api_key


def hash_api_key(api_key: str) -> str:
    """Hash the API key using SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_current_user(
    api_key: Annotated[str, Depends(get_api_key)],
    session: Annotated[Session, Depends(get_db_session)],
) -> User:
    """Retrieve the current user based on the provided API key.
    Raises an HTTPException if the API key is invalid or the user is not found."""
    key_hash = hash_api_key(api_key)
    statement = select(User).where(User.key_hash == key_hash)
    user = session.exec(statement).one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return user


def require_roles(*allowed_roles: Role):
    """Factory function: returns function that checks if the current user has one of the allowed roles."""

    def _dependency(current_user: Annotated[User, Depends(get_current_user)]):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions, {current_user.role} role not in {allowed_roles}",
            )
        return current_user

    return _dependency
