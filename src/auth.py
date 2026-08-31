"""Authentication for the Phenobase API"""

import hashlib
import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select

from src.db import get_db_session
from src.models.tables.user import APIKeyHashRead, User, UserRole


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


def allow_roles(*role: UserRole):
    """Factory function: returns function that returns the
    current user if they have one of the specified roles."""

    def validate_user_role(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in role:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions, {current_user.role} role not in {role}",
            )
        return current_user

    return validate_user_role


def generate_api_key_hash_pair() -> APIKeyHashRead:
    """**Generate API key:**
    Generates a new API key and its SHA-256 hash.
    Requires admin privileges.
    """
    api_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return APIKeyHashRead(api_key=api_key, key_hash=key_hash)
