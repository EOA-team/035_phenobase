import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import UnionType

import pandas as pd
import smbclient
from fastapi import HTTPException, UploadFile, status
from pydantic import BaseModel, TypeAdapter, ValidationError
from sqlmodel import Session, select

from src.models import (
    CropType,
    CropTypeDelete,
    CropTypeInsert,
    CropTypeUpdate,
    UploadModes,
)
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

NAS_UPLOAD_FOLDER = r"drone\phenobase\production\uploads"


class FileType(StrEnum):
    """Phenobase API supported file types."""

    CSV = "csv"
    GEOJSON = "geojson"


class UploadTables(StrEnum):
    """Phenobase API supported tables for Upload"""

    CROP_TYPE = "crop_type"
    CROP_PLOT = "crop_plot"


@dataclass(frozen=True)
class UploadSchema:
    """
    row_model: The Pydantic model used for validating each row of the uploaded file.
    table: The SQLModel table class the validated rows are written to.
    """

    row_model: type[BaseModel] | UnionType
    table: type


TABLE_FILETYPE_MAPPING = {
    UploadTables.CROP_TYPE: FileType.CSV,
    UploadTables.CROP_PLOT: FileType.GEOJSON,
}


# Mapping each UploadTable to its corresponding Pydantic model for validation
UPLOAD_SCHEMA_REGISTRY: dict[UploadTables, UploadSchema] = {
    UploadTables.CROP_TYPE: UploadSchema(
        row_model=CropTypeInsert | CropTypeUpdate | CropTypeDelete, table=CropType
    ),
}


def build_nas_upload_filename(table_name: UploadTables) -> str:
    """Build a filename for uploading to the NAS
    based on the current timestamp (UTC), table name, and file type."""
    now = datetime.now(tz=UTC)
    date_part = now.strftime("%Y%m%d_%H%M%S")  # 20260822_185612
    ms = now.microsecond // 1000  # microseconds -> milliseconds (0-999)
    filetype = get_supported_filetype(table_name)
    return f"{date_part}_{ms:03d}_{table_name}.{filetype.value}"


def get_supported_filetype(table_name: UploadTables) -> FileType:
    """Get the supported file types for a given table."""
    return TABLE_FILETYPE_MAPPING.get(table_name)


def read_upload_file(upload_file: UploadFile) -> pd.DataFrame:
    """Read the uploaded file into a pandas DataFrame based on its file type."""
    df = pd.read_csv(
        upload_file.file,
        sep=None,  # Pandas auto sniffs the separator
        engine="python",
        encoding="utf-8-sig",  # automatically remove Excel BOM artifacts safely
    )

    upload_file.file.seek(0)  # Reset file pointer to the beginning for re-reading
    return df


def append_user_ids(df: pd.DataFrame, current_user_id: int) -> pd.DataFrame:
    """Append user IDs to the DataFrame based on the table name.
    The pydantic row models will use creato_id on insert and updater_id on update, so we add both here."""
    df["creator_id"] = current_user_id
    df["updater_id"] = current_user_id
    return df


def validate_uploaded_file(table_name: UploadTables, upload_file: UploadFile) -> None:
    """Validate the input file for uploading to the Data Platform."""
    supported_table_names = tuple(UploadTables.value for UploadTables in UploadTables)
    supported_filetype = get_supported_filetype(UploadTables(table_name))

    filetype = upload_file.filename.split(".")[-1]

    if table_name not in supported_table_names:
        raise HTTPException(status_code=400, detail=f"Invalid table name: {table_name}")
    if not upload_file.filename.endswith(supported_filetype.value):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format *.{filetype} for table '{table_name}'."
            f"Spported file format:*.{supported_filetype.value}",
        )


def validate_file_content(
    df: pd.DataFrame, table_name: UploadTables
) -> list[BaseModel]:
    """Validate the data in the DataFrame against the corresponding Pydantic row model.
    The row model is determined based on the table name using the UPLOAD_SCHEMA_REGISTRY.
    """

    validation_schema = UPLOAD_SCHEMA_REGISTRY.get(UploadTables(table_name))
    if not validation_schema:
        raise HTTPException(
            status_code=400,
            detail=f"No validation schema found for table '{table_name}'",
        )

    errors = []
    validated = []

    row_adapter = TypeAdapter(validation_schema)

    records = df.to_dict(orient="records")
    for index, record in enumerate(records):
        try:
            validated.append(row_adapter.validate_python([record]))

        except ValidationError as row_error:
            line = index + 2  # +2 to account for header and 0-indexing
            for err in row_error.errors(include_url=False, include_context=False):
                errors.append(
                    {
                        "type": err.get("type", "value_error"),
                        "loc": ("line", line, *err.get("loc", ())),
                        "msg": err.get("msg", "Unknown validation error"),
                        "input": record,
                    }
                )
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=errors
        )
    return validated


def write_file_to_nas(table_name: UploadTables, data: bytes) -> None:
    """Upload a any file to the NAS"""
    upload_path = build_unc_path(
        hostname=os.getenv("NAS_RECKENHOLZ"),
        share="Data-EODrone",
        folder=NAS_UPLOAD_FOLDER,
    )
    filename = build_nas_upload_filename(UploadTables(table_name))
    upload_file_path = Path(upload_path) / filename

    connect_to_nas(user_type=NasUser.SERVICE, password=NasPw.SERVICE)
    with smbclient.open_file(upload_file_path, "wb", encoding="utf-8") as f:
        f.write(data)


def export_db_table_to_csv(session: Session, table_name: UploadTables) -> str:
    """Export a database table to a CSV file."""
    sql_table = UPLOAD_SCHEMA_REGISTRY.get(UploadTables(table_name)).table
    rows = session.exec(select(sql_table)).all()
    df = pd.DataFrame([row.model_dump() for row in rows])
    csv_file = df.to_csv(index=False, encoding="utf-8")
    return csv_file


def write_to_database(
    session: Session,
    table_name: UploadTables,
    rows: list[BaseModel],
) -> None:
    """Write validated rows to the database as insert/update/delete.

    Works for any table registered in UPLOAD_SCHEMA_REGISTRY: the target
    table class comes from the registry, and each row model carries its
    own fields, so model_dump() always produces valid column values.

    All rows are applied within one session; a single commit at the end
    makes the whole file atomic: either every row lands or none does.
    """
    table = UPLOAD_SCHEMA_REGISTRY[table_name].table

    for row in rows:
        mode = row.mode  # every Insert/Update/Delete model has one

        if mode == UploadModes.INSERT:
            session.add(table(**row.model_dump(exclude={"mode"})))

        elif mode == UploadModes.UPDATE:
            row_id = row.id
            existing = session.get(table, row_id)
            if existing is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Cannot update: {table.__tablename__} id={row_id} does not exist",
                )
            for field, value in row.model_dump(exclude={"mode", "id"}).items():
                setattr(existing, field, value)

        elif mode == UploadModes.DELETE:
            row_id = row.id
            existing = session.get(table, row_id)
            if existing is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Cannot delete: {table.__tablename__} id={row_id} does not exist",
                )
            session.delete(existing)

    session.commit()
