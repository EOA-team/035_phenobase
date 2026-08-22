"""
Docstring for src.main
"""

from typing import Annotated

from fastapi import Depends, FastAPI

from src.api import Role
from src.auth import allow_roles, generate_api_key_hash_pair, get_current_user
from src.models import APIKeyHashRead, UserRead

app = FastAPI(
    title="Phenobase API",
    description="API allows you to interact with the Phenobase Data Platform",
)


@app.get("/")
def api_info():
    """**Basic API Information:**
    Returns basic information plus navigation links.
    """
    return {
        "name": app.title,
        "version": app.version,
        "description": app.description,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
    }


@app.get("/health", status_code=200)
def health_check():
    """**Health check:**
    Returns 200 with {status: ok} if the API is running
    """
    return {"status": "ok"}


@app.get("/auth/me", response_model=UserRead)
def auth_me(current_user: Annotated[UserRead, Depends(get_current_user)]):
    """**Get current user:**
    Returns the current user based on the provided API key.
    Requires an 'X-API-Key' header with a valid API key.
    """
    return current_user


@app.get(
    "/admin/generate-api-key",
    response_model=APIKeyHashRead,
    dependencies=[Depends(allow_roles(Role.admin))],
)
def api_key_hash_pair() -> APIKeyHashRead:
    """**Generate API key:**
    Generates a new API key and its SHA-256 hash.
    Requires admin privileges.
    """
    return generate_api_key_hash_pair()
