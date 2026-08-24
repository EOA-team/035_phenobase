"""
Docstring for src.main
"""

from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Response, UploadFile
from sqlmodel import Session

from src.auth import allow_roles, generate_api_key_hash_pair, get_current_user
from src.data_upload import (
    append_user_ids,
    read_upload_file,
    validate_file_content,
    validate_uploaded_file,
    write_file_to_nas,
    write_to_database,
)
from src.db import get_db_session
from src.db_utils import get_db_table_as_pd, table_is_empty
from src.models.registry import UploadTables
from src.models.tables.user import APIKeyHashRead, UserRead, UserRole

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
    dependencies=[Depends(allow_roles(UserRole.admin))],
    tags=["Admin"],
)
def api_key_hash_pair() -> APIKeyHashRead:
    """**Generate API key:**
    Generates a new API key and its SHA-256 hash.
    Requires admin privileges.
    """
    return generate_api_key_hash_pair()


@app.get(
    "/data/{table_name}",
    dependencies=[
        Depends(allow_roles(UserRole.reader, UserRole.writer, UserRole.admin))
    ],
)
def get_table_data(
    table_name: UploadTables,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[UserRead, Depends(get_current_user)],
):
    """**Get table data:**
    Returns the rows of the specified table as CSV.
    The response schema is resolved at runtime based on the table name.
    Require at admin privileges for users table
    Require at least reader privileges for all other tables.
    """
    if table_name == UploadTables.USER and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to read user data.",
        )
    if table_is_empty(session=session, table_name=table_name):
        return Response(
            content=f"Table '{table_name}' is currently empty.",
            status_code=200,
        )
    df = get_db_table_as_pd(session=session, table_name=table_name)
    return Response(
        content=df.to_csv(index=False, sep=";", encoding="utf-8"),
        media_type="text/csv",
    )


@app.post("/data/upload/{table_name}")
def upload_file(
    table_name: UploadTables,
    upload_file: UploadFile,
    current_user: Annotated[UserRead, Depends(allow_roles(UserRole.writer, UserRole.admin))],
    session: Annotated[Session, Depends(get_db_session)],
):
    """**Upload data:**
    Uploads data to the specified table in Database
    and saves the uploaded files to the NAS for Logging.

    Requires writer privileges (admin for the users table).
    """
    if table_name == UploadTables.USER and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to manage users.",
        )
    validate_uploaded_file(upload_file=upload_file, table_name=table_name)
    df = read_upload_file(upload_file=upload_file).pipe(
        append_user_ids,
        current_user_id=current_user.id,
        current_user=current_user.firstname + " " + current_user.lastname,
    )

    validated_rows = validate_file_content(df=df, table_name=table_name)
    write_to_database(session=session, table_name=table_name, rows=validated_rows)

    # Write the uploaded file to NAS for logging
    upload_csv = df.to_csv(index=False, sep=";", encoding="utf-8")
    write_file_to_nas(table_name=table_name, data=upload_csv.encode("utf-8"))

    return Response(
        content=f"File {upload_file.filename}  successfully commited to Data Platform",
        status_code=200,
    )
