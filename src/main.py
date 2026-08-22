"""
Docstring for src.main
"""

from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Response, UploadFile
from sqlmodel import Session

from src.api import Role
from src.auth import allow_roles, generate_api_key_hash_pair, get_current_user
from src.data_upload import (
    UploadTables,
    append_user_ids,
    export_db_table_to_csv,
    read_upload_file,
    validate_file_content,
    validate_uploaded_file,
    write_file_to_nas,
    write_to_database,
)
from src.db import get_db_session
from src.models import APIKeyHashRead, UserRead

load_dotenv()

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
def upload_file(
    table_name: UploadTables,
    upload_file: UploadFile,
    current_user: Annotated[UserRead, Depends(allow_roles(Role.writer))],
    session: Annotated[Session, Depends(get_db_session)],
):
    """**Upload data:**
    Uploads data to the specified table in Database
    and saves the uploaded files to the NAS for Logging.

    Requires writer privileges.
    """
    validate_uploaded_file(upload_file=upload_file, table_name=table_name)
    df = read_upload_file(upload_file=upload_file).pipe(
        append_user_ids, current_user_id=current_user.id
    )

    validated_rows = validate_file_content(df=df, table_name=table_name)
    write_to_database(session=session, table_name=table_name, rows=validated_rows)
    table_csv = export_db_table_to_csv(session=session, table_name=table_name)

    write_file_to_nas(table_name=table_name, data=table_csv.encode("utf-8"))

    return Response(
        content=f"File {upload_file.filename} uploaded successfully to Data Platform",
        status_code=200,
    )
