"""
Docstring for src.main
"""

import os
from pathlib import Path
from typing import Annotated

import smbclient
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Response, UploadFile

from src.api import Role
from src.auth import allow_roles, generate_api_key_hash_pair, get_current_user
from src.data_upload import (
    Tables,
    build_nas_upload_filename,
    get_supported_filetype,
)
from src.models import APIKeyHashRead, UserRead
from src.nas_helper import (
    Password as NasPw,
)
from src.nas_helper import (
    User as NasUser,
)
from src.nas_helper import (
    build_unc_path,
    connect_to_nas,
)

load_dotenv()


UPLOAD_FOLDER = r"drone\phenobase\production\uploads"


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


@app.get("/auth/me", response_model=UserRead, tags=["Authentication"])
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
    tags=["Admin"],
)
def api_key_hash_pair() -> APIKeyHashRead:
    """**Generate API key:**
    Generates a new API key and its SHA-256 hash.
    Requires admin privileges.
    """
    return generate_api_key_hash_pair()


@app.post("/data/upload/{table_name}")
def upload_csv_to_nas(
    table_name: str,
    upload_file: UploadFile,
    current_user: Annotated[UserRead, Depends(allow_roles(Role.writer))],
):
    """**Upload data:**
    Uploads data to the specified table.
    Requires admin privileges.
    """

    supported_table_names = tuple(Tables.value for Tables in Tables)
    supported_filetype = get_supported_filetype(Tables(table_name))

    filetype = upload_file.filename.split(".")[-1]

    if table_name not in supported_table_names:
        raise HTTPException(status_code=400, detail=f"Invalid table name: {table_name}")
    if not upload_file.filename.endswith(supported_filetype.value):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format *.{filetype} for table '{table_name}'."
            f"Spported file format:*.{supported_filetype.value}",
        )

    upload_path = build_unc_path(
        hostname=os.getenv("NAS_RECKENHOLZ"), share="Data-EODrone", folder=UPLOAD_FOLDER
    )
    filename = build_nas_upload_filename(Tables(table_name))
    upload_file_path = Path(upload_path) / filename

    connect_to_nas(user_type=NasUser.SERVICE, password=NasPw.SERVICE)
    with smbclient.open_file(upload_file_path, "wb", encoding="utf-8") as f:
        f.write(upload_file.file.read())

    return Response(
        content=f"File {upload_file.filename} uploaded successfully to NAS ",
        status_code=200,
    )
